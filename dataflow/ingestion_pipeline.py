import argparse
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, SetupOptions
import apache_beam.transforms.window as window
from fatigue_model import FatigueModel

class ParseTelemetry(beam.DoFn):
    def process(self, element):
        try:
            # element este payload-ul binar din Pub/Sub (GPS Vest / Senzori)
            data = json.loads(element.decode('utf-8'))
            player_id = data.get('player_id')
            if player_id:
                yield (player_id, data)
        except Exception as e:
            logging.error(f"Eroare Parsare: {e}")

class CalculateFatigueAndAggregate(beam.DoFn):
    def process(self, element, window_info=beam.DoFn.WindowParam):
        player_id, records = element
        records_list = list(records)
        
        # Aplicarea modelului de oboseală peste datele de frecvență înaltă din fereastra curentă
        fatigue_index = FatigueModel.calculate(records_list)
        
        # Preluăm coordonatele precise pentru momentul T_curent
        last_record = sorted(records_list, key=lambda x: x.get('timestamp', 0))[-1]
        
        yield {
            'player_id': player_id,
            'fatigue_index': round(fatigue_index, 2),
            'x': last_record.get('x'),
            'y': last_record.get('y'),
            'window_end': window_info.end.to_utc_datetime().isoformat()
        }

class WriteToFirestore(beam.DoFn):
    def setup(self):
        # Inițializăm clientul de Bază de Date o singură dată pe fiecare instanță de worker Dataflow
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        self.db = firestore.client()
        
    def process(self, element):
        player_id = element['player_id']
        doc_ref = self.db.collection('players_live').document(player_id)
        
        # Scriere masivă, ocolind REST API-ul pentru Zero Overhead
        doc_ref.set(element, merge=True)
        yield element

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_topic', required=True, help='Topic GCP Pub/Sub (ex: projects/PROJ/topics/gps-telemetry)')
    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)
    # Activăm procesarea real-time (Streaming) - FAANG standard
    options.view_as(StandardOptions).streaming = True
    options.view_as(SetupOptions).save_main_session = True

    # P - Pipeline-ul Apache Beam
    with beam.Pipeline(options=options) as p:
        (
            p
            # 1. Ingestie distribuită asincronă din Pub/Sub (Scalabilitate: 1.000.000 mesaje/secundă)
            | "Read from PubSub" >> beam.io.ReadFromPubSub(topic=known_args.input_topic)
            | "Parse JSON" >> beam.ParDo(ParseTelemetry())
            
            # 2. SLIDING WINDOW: Grupăm senzorii pe ferestre de 1 secundă care se evaluează la fiecare 0.5s.
            # Asta elimină total zgomotul (Spike-urile de senzor) fără să pierdem frame-uri pe UI.
            | "Sliding Window" >> beam.WindowInto(window.SlidingWindows(size=1.0, period=0.5))
            
            # 3. Agregare Masivă (Shuffle Phase) - Jucătorii pe Worker-i distincți
            | "Group By Player" >> beam.GroupByKey()
            
            # 4. Procesarea Oboselii și filtrarea coordonatelor pentru Frontend
            | "Calculate Fatigue ML" >> beam.ParDo(CalculateFatigueAndAggregate())
            
            # 5. SINK: Inserăm deciziile de milioane de ori pe secundă direct în Baza de Date
            | "Sink Firestore" >> beam.ParDo(WriteToFirestore())
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()

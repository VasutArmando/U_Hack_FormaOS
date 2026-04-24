import 'package:flutter/material.dart';
import 'dart:html' as html;
import 'dart:ui' as ui;

class LookerDashboard extends StatelessWidget {
  final String embedUrl;

  const LookerDashboard({super.key, required this.embedUrl});

  @override
  Widget build(BuildContext context) {
    // Generăm un ID unic bazat pe URL
    final String viewId = 'looker-iframe-\$embedUrl';
    
    // Înregistrăm IFrame-ul nativ pentru web
    // ignore: undefined_prefixed_name
    ui.platformViewRegistry.registerViewFactory(
      viewId,
      (int viewId) => html.IFrameElement()
        ..src = embedUrl
        ..style.border = 'none'
        ..style.height = '100%'
        ..style.width = '100%',
    );

    return Scaffold(
      backgroundColor: Colors.white,
      body: HtmlElementView(viewType: viewId),
    );
  }
}

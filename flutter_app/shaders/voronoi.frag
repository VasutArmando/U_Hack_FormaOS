#include <flutter/runtime_effect.glsl>

uniform vec2 u_resolution;

// Array ce stochează (x,y) normalizate pentru cei 22 de jucători.
// Index 0-10 (Echipa Home), Index 11-21 (Echipa Away).
// GPU-ul procesează asta paralel pe fiecare pixel al ecranului!
uniform vec2 u_players[22];

out vec4 fragColor;

void main() {
    // Coordonate normalizate (0.0 -> 1.0) pentru pixelul curent
    vec2 st = FlutterFragCoord().xy / u_resolution;
    
    // Corectăm Aspect Ratio pentru a nu distorsiona calculul distanței euclidiene pe un teren dreptunghiular
    float aspect = u_resolution.x / u_resolution.y;
    vec2 st_corrected = vec2(st.x * aspect, st.y);
    
    float minDistHome = 999.0;
    float minDistAway = 999.0;
    
    // Aflăm distanța minimă către cel mai apropiat jucător al gazdelor
    for(int i = 0; i < 11; i++) {
        if(u_players[i].x >= 0.0) { // Ignorăm jucătorii absenți/eliminați (-1.0)
            vec2 p_corrected = vec2(u_players[i].x * aspect, u_players[i].y);
            float d = distance(st_corrected, p_corrected);
            minDistHome = min(minDistHome, d);
        }
    }
    
    // Aflăm distanța minimă către cel mai apropiat jucător al oaspeților
    for(int i = 11; i < 22; i++) {
        if(u_players[i].x >= 0.0) {
            vec2 p_corrected = vec2(u_players[i].x * aspect, u_players[i].y);
            float d = distance(st_corrected, p_corrected);
            minDistAway = min(minDistAway, d);
        }
    }
    
    // Paletă de culori Premium pentru Pitch Control
    vec4 homeColor = vec4(1.0, 1.0, 1.0, 0.12);     // Alb-ul 'U' Cluj
    vec4 awayColor = vec4(0.55, 0.0, 0.0, 0.12);    // Vișiniu CFR
    vec4 contestedColor = vec4(0.83, 0.68, 0.21, 0.25); // Auriu (Zone Dispute/Tensionate)

    float diff = minDistHome - minDistAway;
    float boundaryWidth = 0.015; // Lățimea zonei de "Glow" între celule (Anti-aliasing)
    
    // Smoothstep creează un gradient vizual fluid între celule, specific graficii FAANG
    if (abs(diff) < boundaryWidth) {
        float blend = smoothstep(0.0, boundaryWidth, abs(diff));
        fragColor = mix(contestedColor, (diff < 0.0 ? homeColor : awayColor), blend);
    } else if (diff < 0.0) {
        fragColor = homeColor; // Gazdele controlează zona
    } else {
        fragColor = awayColor; // Oaspeții controlează zona
    }
}

# =============================================================================
# EMORPHOSIS — Extrator dos Píxeis Verdes da Borda Exterior do Brasil (home-bg.png)
# Analisa assets/img/home-bg.png (2560x1440), isola os píxeis verdes da figura
# do Brasil e gera assets/data/brazil_map_bounds.json com os limites exatos
# por linha (rows[y] = [leftX, rightX]) e por coluna (cols[x] = [topY, bottomY]).
# =============================================================================

$code = @"
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Text;

public class BrazilBorderExtractorScript {
    public static void Build(string imgPath, string outJsonPath) {
        Bitmap bmp = new Bitmap(imgPath);
        int W = bmp.Width;
        int H = bmp.Height;

        bool[,] isGreen = new bool[W, H];
        for (int y = 310; y <= 1120; y++) {
            for (int x = 485; x <= 1350; x++) {
                if (x <= 656 && y >= 632 && y <= 736) continue;
                if (x <= 885 && y >= 1008 && y <= 1105) continue;
                Color c = bmp.GetPixel(x, y);
                if (c.G >= 175 && c.G > c.R + 80) {
                    isGreen[x, y] = true;
                }
            }
        }

        bool[,] isMapStroke = new bool[W, H];
        for (int y = 315; y <= 1115; y++) {
            for (int x = 490; x <= 1345; x++) {
                if (!isGreen[x, y]) continue;

                if (y >= 516 && y <= 690) {
                    double line1X = 652.0 + (688.0 - y) * (116.0 / 170.0);
                    if (Math.Abs(x - line1X) <= 4.0 && y > 612) continue;
                }
                if (y >= 1042 && y <= 1080 && x <= 908) {
                    double line2X = 882.0 + (1070.0 - y) * (119.0 / 142.0);
                    if (Math.Abs(x - line2X) <= 4.5) continue;
                }

                bool nearGridX = (Math.Abs(x - 532) <= 4 || Math.Abs(x - 679) <= 3 || Math.Abs(x - 825) <= 3 || Math.Abs(x - 972) <= 3 || Math.Abs(x - 1118) <= 3 || Math.Abs(x - 1265) <= 4);
                bool nearGridY = (Math.Abs(y - 335) <= 4 || Math.Abs(y - 513) <= 3 || Math.Abs(y - 691) <= 3 || Math.Abs(y - 869) <= 3 || Math.Abs(y - 1047) <= 4);

                if (nearGridX || nearGridY) {
                    int offGridNeighbors = 0;
                    for (int dy = -5; dy <= 5; dy++) {
                        for (int dx = -5; dx <= 5; dx++) {
                            int nx = x + dx, ny = y + dy;
                            bool nGridX = (Math.Abs(nx - 532) <= 4 || Math.Abs(nx - 679) <= 3 || Math.Abs(nx - 825) <= 3 || Math.Abs(nx - 972) <= 3 || Math.Abs(nx - 1118) <= 3 || Math.Abs(nx - 1265) <= 4);
                            bool nGridY = (Math.Abs(ny - 335) <= 4 || Math.Abs(ny - 513) <= 3 || Math.Abs(ny - 691) <= 3 || Math.Abs(ny - 869) <= 3 || Math.Abs(ny - 1047) <= 4);
                            if (!nGridX && !nGridY && isGreen[nx, ny]) offGridNeighbors++;
                        }
                    }
                    if (offGridNeighbors < 10) continue;
                }

                int count = 0;
                for (int dy = -2; dy <= 2; dy++) {
                    for (int dx = -2; dx <= 2; dx++) {
                        if (isGreen[x + dx, y + dy]) count++;
                    }
                }
                if (count >= 7) {
                    isMapStroke[x, y] = true;
                }
            }
        }

        bool[,] visited = new bool[W, H];
        Queue<Point> q = new Queue<Point>();
        Point[] seeds = new Point[] {
            new Point(783, 326),
            new Point(500, 588),
            new Point(1332, 602),
            new Point(928, 1104),
            new Point(1036, 934),
            new Point(1136, 882),
            new Point(1235, 498),
            new Point(956, 355)
        };
        foreach (var s in seeds) {
            for (int dy = -6; dy <= 6; dy++) {
                for (int dx = -6; dx <= 6; dx++) {
                    if (isMapStroke[s.X + dx, s.Y + dy] && !visited[s.X + dx, s.Y + dy]) {
                        visited[s.X + dx, s.Y + dy] = true;
                        q.Enqueue(new Point(s.X + dx, s.Y + dy));
                    }
                }
            }
        }

        while (q.Count > 0) {
            Point p = q.Dequeue();
            for (int dy = -4; dy <= 4; dy++) {
                for (int dx = -4; dx <= 4; dx++) {
                    int nx = p.X + dx, ny = p.Y + dy;
                    if (nx >= 490 && nx <= 1345 && ny >= 315 && ny <= 1115) {
                        if (isMapStroke[nx, ny] && !visited[nx, ny]) {
                            visited[nx, ny] = true;
                            q.Enqueue(new Point(nx, ny));
                        }
                    }
                }
            }
        }

        int minX = 9999, maxX = 0, minY = 9999, maxY = 0;
        int[] rowMinX = new int[H];
        int[] rowMaxX = new int[H];
        for (int y = 0; y < H; y++) { rowMinX[y] = 9999; rowMaxX[y] = 0; }

        int[] colMinY = new int[W];
        int[] colMaxY = new int[W];
        for (int x = 0; x < W; x++) { colMinY[x] = 9999; colMaxY[x] = 0; }

        for (int y = 315; y <= 1115; y++) {
            for (int x = 490; x <= 1345; x++) {
                if (visited[x, y]) {
                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                    if (x < rowMinX[y]) rowMinX[y] = x;
                    if (x > rowMaxX[y]) rowMaxX[y] = x;
                    if (y < colMinY[x]) colMinY[x] = y;
                    if (y > colMaxY[x]) colMaxY[x] = y;
                }
            }
        }

        for (int y = minY; y <= maxY; y++) {
            if (rowMinX[y] > rowMaxX[y] && y > minY) {
                rowMinX[y] = rowMinX[y - 1];
                rowMaxX[y] = rowMaxX[y - 1];
            }
        }
        for (int x = minX; x <= maxX; x++) {
            if (colMinY[x] > colMaxY[x] && x > minX) {
                colMinY[x] = colMinY[x - 1];
                colMaxY[x] = colMaxY[x - 1];
            }
        }

        StringBuilder sb = new StringBuilder();
        sb.Append("{\n");
        sb.AppendFormat("  \"imageWidth\": {0},\n  \"imageHeight\": {1},\n", W, H);
        sb.AppendFormat("  \"pixelBounds\": {{ \"minX\": {0}, \"maxX\": {1}, \"minY\": {2}, \"maxY\": {3} }},\n", minX, maxX, minY, maxY);
        sb.Append("  \"geoExtremes\": { \"latNorth\": 5.2718, \"latSouth\": -33.7512, \"lonWest\": -73.9828, \"lonEast\": -34.7931 },\n");

        sb.Append("  \"rows\": {\n");
        for (int y = minY; y <= maxY; y++) {
            sb.AppendFormat("    \"{0}\": [{1}, {2}]{3}\n", y, rowMinX[y], rowMaxX[y], (y < maxY ? "," : ""));
        }
        sb.Append("  },\n");

        sb.Append("  \"cols\": {\n");
        for (int x = minX; x <= maxX; x++) {
            sb.AppendFormat("    \"{0}\": [{1}, {2}]{3}\n", x, colMinY[x], colMaxY[x], (x < maxX ? "," : ""));
        }
        sb.Append("  }\n");
        sb.Append("}\n");

        File.WriteAllText(outJsonPath, sb.ToString(), Encoding.UTF8);
        bmp.Dispose();
    }
}
"@
Add-Type -TypeDefinition $code -ReferencedAssemblies System.Drawing
$root = Split-Path -Parent $PSScriptRoot
[BrazilBorderExtractorScript]::Build(
    (Join-Path $root "assets\img\home-bg.png"),
    (Join-Path $root "assets\data\brazil_map_bounds.json")
)
Write-Host "[OK] assets/data/brazil_map_bounds.json atualizado!"

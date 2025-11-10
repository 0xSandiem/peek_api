import numpy as np
from sklearn.cluster import KMeans


class ColorAnalyzer:
    @staticmethod
    def analyze(img_array):
        try:
            if img_array.size == 0:
                raise ValueError("Empty image array")

            pixels = img_array.reshape(-1, 3)

            n_clusters = min(5, len(pixels))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(pixels)

            colors = kmeans.cluster_centers_.astype(int)
            hex_colors = [f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}" for c in colors]

            brightness = int(
                np.mean(
                    0.299 * img_array[:, :, 0]
                    + 0.587 * img_array[:, :, 1]
                    + 0.114 * img_array[:, :, 2]
                )
            )

            brightness = max(0, min(255, brightness))

            return {"dominant_colors": hex_colors, "brightness": brightness}

        except Exception as e:
            raise ValueError(f"Color analysis failed: {str(e)}")

import type { MapRef } from "react-map-gl/maplibre";

function createPulsingDot(
  map: MapRef,
  size: number = 85,
  innerColor: { r: number; g: number; b: number } = { r: 70, g: 130, b: 180 },
  outerColor: { r: number; g: number; b: number } = { r: 70, g: 130, b: 180 },
  duration: number = 800, // Expansion phase duration
  idleTime: number = 3000 // Pause duration (3000ms or 3 seconds)
) {
  const totalDuration = duration + idleTime; // Total cycle duration.

  return {
    width: size,
    height: size,
    data: new Uint8Array(size * size * 4),

    onAdd: function (): void {
      const canvas = document.createElement("canvas");
      canvas.width = this.width;
      canvas.height = this.height;
      this.context = canvas.getContext("2d") as CanvasRenderingContext2D;
    },

    render: function (): boolean {
      const currentTime = performance.now() % totalDuration;

      // Determine if we are in the expansion phase or the idle phase.
      const isExpanding = currentTime <= duration;
      const t = isExpanding ? currentTime / duration : 0; // Normalized time for expansion.

      const radius = (size / 2) * 0.3; // Static inner circle radius.
      const outerRadius = isExpanding ? (size / 2) * 0.7 * t + radius : 0; // Outer circle expands only during the animation phase.
      const context = this.context;

      // Clear the canvas.
      context.clearRect(0, 0, this.width, this.height);

      // Draw the outer circle (stroke only during expansion phase).
      if (isExpanding) {
        context.beginPath();
        context.arc(this.width / 2, this.height / 2, outerRadius, 0, Math.PI * 2);
        context.strokeStyle = `rgba(${outerColor.r}, ${outerColor.g}, ${outerColor.b}, ${1 - t})`;
        context.lineWidth = 4; // Outer circle stroke thickness.
        context.stroke();
      }

      // Draw the inner circle (static).
      context.beginPath();
      context.arc(this.width / 2, this.height / 2, radius, 0, Math.PI * 2);
      context.fillStyle = `rgba(${innerColor.r}, ${innerColor.g}, ${innerColor.b}, 1)`;
      context.strokeStyle = "white";
      context.lineWidth = 2;
      context.fill();
      context.stroke();

      // Update this image's data with data from the canvas.
      this.data = context.getImageData(0, 0, this.width, this.height).data;

      // Continuously repaint the map for smooth animation.
      map.triggerRepaint();

      // Return `true` to let the map know that the image was updated.
      return true;
    },
  };
}

export default createPulsingDot;

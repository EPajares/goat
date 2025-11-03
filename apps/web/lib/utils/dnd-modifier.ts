import type { Modifier } from '@dnd-kit/core';
import { getEventCoordinates } from '@dnd-kit/utilities';

export const createSnapToCursorModifier = (snapPosition: 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight' | 'topCenter' | 'bottomCenter'): Modifier => {
  return ({
    activatorEvent,
    draggingNodeRect,
    transform,
  }) => {
    if (draggingNodeRect && activatorEvent) {
      const activatorCoordinates = getEventCoordinates(activatorEvent);

      if (!activatorCoordinates) {
        return transform;
      }

      let offsetX = 0;
      let offsetY = 0;

      switch (snapPosition) {
        case 'topLeft':
          offsetX = activatorCoordinates.x - draggingNodeRect.left;
          offsetY = activatorCoordinates.y - draggingNodeRect.top;
          break;
        case 'topRight':
          offsetX = activatorCoordinates.x - draggingNodeRect.right;
          offsetY = activatorCoordinates.y - draggingNodeRect.top;
          break;
        case 'bottomLeft':
          offsetX = activatorCoordinates.x - draggingNodeRect.left;
          offsetY = activatorCoordinates.y - draggingNodeRect.bottom;
          break;
        case 'bottomRight':
          offsetX = activatorCoordinates.x - draggingNodeRect.right;
          offsetY = activatorCoordinates.y - draggingNodeRect.bottom;
          break;
        case 'topCenter':
          offsetX = activatorCoordinates.x - (draggingNodeRect.left + draggingNodeRect.width / 2);
          offsetY = activatorCoordinates.y - draggingNodeRect.top;
          break;
        case 'bottomCenter':
          offsetX = activatorCoordinates.x - (draggingNodeRect.left + draggingNodeRect.width / 2);
          offsetY = activatorCoordinates.y - draggingNodeRect.bottom;
          break;
      }

      return {
        ...transform,
        x: transform.x + offsetX,
        y: transform.y + offsetY,
      };
    }

    return transform;
  };
};

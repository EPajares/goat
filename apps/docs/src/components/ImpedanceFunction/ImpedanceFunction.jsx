import React, { useEffect, useRef, useState } from 'react';

export default function ImpedanceFunction({ initialFunction = 'gaussian', initialSensitivity = 300000 }) {
  const [impedanceFunction, setImpedanceFunction] = useState(initialFunction);
  const [sensitivity, setSensitivity] = useState(initialSensitivity);
  const canvasRef = useRef(null);

  // Define the canvas dimensions
  const width = 700;
  const height = 350;
  const padding = 40;
  
  // Max travel time in minutes
  const MAX_TRAVEL_TIME_MIN = 30;
  // Display up to approximately 20 minutes on the x-axis
  const DISPLAY_MAX_MIN = 30;
  // Max sensitivity value
  const MAX_SENSITIVITY = 1000000;

  // Calculate values based on the selected function and sensitivity
  const calculateValues = () => {
    // Generate data points for minutes
    const travelTimesMinutes = [];
    for (let t = 0; t <= DISPLAY_MAX_MIN; t += 0.5) {
      travelTimesMinutes.push(t);
    }
    
    let values = [];

    switch(impedanceFunction) {
      case 'gaussian':
        // For gaussian (gravity): normalize travel time by 30 minutes and sensitivity by 1 million
        const normalizedSensitivity = sensitivity / MAX_SENSITIVITY;
        values = travelTimesMinutes.map(t => {
          const normalizedTime = t / MAX_TRAVEL_TIME_MIN;
          return Math.exp(-10 * (Math.pow(normalizedTime, 2) / normalizedSensitivity));
        });
        break;
      case 'linear':
        // Linear: max(0, 1 - t/T) where T is maximum travel time
        // Linear function doesn't depend on sensitivity
        values = travelTimesMinutes.map(t => Math.max(0, 1 - (t / MAX_TRAVEL_TIME_MIN)));
        break;
      case 'exponential':
        // Exponential: exp(-β * t) - normalize travel time by 30 minutes and sensitivity by 1 million
        const expNormalizedSensitivity = sensitivity / MAX_SENSITIVITY;
        values = travelTimesMinutes.map(t => {
          const normalizedTime = t / MAX_TRAVEL_TIME_MIN;
          return Math.exp(-expNormalizedSensitivity * 5 * normalizedTime);
        });
        break;
      case 'power':
        // Power: normalize the power coefficient by max sensitivity (1 million), don't normalize travel time
        const powerCoefficient = sensitivity / MAX_SENSITIVITY;
        values = travelTimesMinutes.map(t => t <= 1 ? 1 : Math.pow(t , -powerCoefficient * 2));
        break;
      default:
        const defaultNormalizedSensitivity = sensitivity / MAX_SENSITIVITY;
        values = travelTimesMinutes.map(t => {
          const normalizedTime = t / MAX_TRAVEL_TIME_MIN;
          return Math.exp(-defaultNormalizedSensitivity * 10 * Math.pow(normalizedTime, 2));
        });
    }

    return { travelTimesMinutes, values };
  };

  // Draw the graph on the canvas
  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, width, height);

    const { travelTimesMinutes, values } = calculateValues();

    // Draw axes inset by 2*padding
    const xStart = 2 * padding;
    const xEnd = width - 2 * padding;
    ctx.beginPath();
    ctx.moveTo(xStart, padding);
    ctx.lineTo(xStart, height - padding);
    ctx.lineTo(xEnd, height - padding);
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw title
    ctx.fillStyle = '#333';
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    //ctx.fillText(`${impedanceFunction.charAt(0).toUpperCase() + impedanceFunction.slice(1)} impedance function`, width / 2, padding / 2);

    // Draw labels
    ctx.font = '12px Arial';

    // Draw Y-axis label
    ctx.save();
    ctx.translate(padding, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText('Willingness to walk', 0, 0);
    ctx.restore();

    // X-axis label
    ctx.fillText('Minutes', width / 2, height - 5);

    // Draw Y-axis ticks and labels up to 1000%
    ctx.textAlign = 'right';
    const yTicks = 10;
    for (let i = 0; i <= yTicks; i++) {
      const y = height - padding - (i * (height - 2 * padding) / yTicks);
      ctx.beginPath();
      ctx.moveTo(xStart - 5, y);
      ctx.lineTo(xStart, y);
      ctx.stroke();
      ctx.fillText(`${i * 10}%`, xStart - 8, y + 4);
    }

    // Draw X-axis ticks and labels
    ctx.textAlign = 'center';
    const graphWidth = xEnd - xStart;
    const xScale = graphWidth / DISPLAY_MAX_MIN;
    for (let min = 0; min <= DISPLAY_MAX_MIN; min += 2) {
      const x = xStart + min * xScale;
      ctx.beginPath();
      ctx.moveTo(x, height - padding);
      ctx.lineTo(x, height - padding + 5);
      ctx.stroke();
      ctx.fillText(`${min}`, x, height - padding + 20);
    }

    // Draw the line graph
    ctx.beginPath();
    for (let i = 0; i < travelTimesMinutes.length; i++) {
      const x = xStart + travelTimesMinutes[i] * xScale;
      const y = height - padding - values[i] * (height - 2 * padding);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.strokeStyle = '#2BB381';
    ctx.lineWidth = 3;
    ctx.stroke();
  };

  // Update the graph when impedance function or sensitivity changes
  useEffect(() => {
    drawGraph();
  }, [impedanceFunction, sensitivity]);

  return (
    <div style={{ marginBottom: '30px' }}>
      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Impedance Function:</label>
        <select 
          value={impedanceFunction} 
          onChange={(e) => setImpedanceFunction(e.target.value)}
          style={{ padding: '8px', borderRadius: '4px', marginRight: '20px' }}
        >
          <option value="gaussian">Gaussian</option>
          <option value="linear">Linear</option>
          <option value="exponential">Exponential</option>
          <option value="power">Power</option>
        </select>
        
        {/* Only show sensitivity slider for functions that depend on it */}
        {impedanceFunction !== 'linear' && (
          <>
            <label style={{ marginRight: '10px', fontWeight: 'bold' }}>Sensitivity (β):</label>
            <input 
              type="range" 
              min="10000" 
              max={MAX_SENSITIVITY} 
              step="10000" 
              value={sensitivity} 
              onChange={(e) => setSensitivity(Number(e.target.value))} 
              style={{ width: '150px', verticalAlign: 'middle', accentColor: '#2BB381'}}
            />
            <span style={{ marginLeft: '10px' }}>{sensitivity.toLocaleString()}</span>
          </>
        )}
      </div>
      
      <canvas ref={canvasRef} width={width} height={height} style={{ border: '0px solid #ddd', borderRadius: '0px',display: 'block',margin: '0 auto'   }} />
      
      <div style={{ marginTop: '10px', fontSize: '14px', color: '#ddd' }}>
  
      </div>
    </div>
  );
}
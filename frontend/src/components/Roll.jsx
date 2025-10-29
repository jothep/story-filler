// src/components/Roll.jsx
// A purely presentational component that renders the div structure
// required for the parallax scrolling background effect defined in `Roll.css`.

function Roll() {
  return (
    <div className="parallax-container">
      <div className="parallax-layer layer-1"></div>
      <div className="parallax-layer layer-2"></div>
      <div className="parallax-layer layer-3"></div>
      <div className="parallax-layer layer-4"></div>
    </div>
  );
}

export default Roll;

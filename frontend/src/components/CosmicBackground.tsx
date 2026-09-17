import React, { useEffect, useRef } from 'react';

interface CosmicBackgroundProps {
  variant?: 'landing' | 'dashboard' | 'subtle';
  className?: string;
}

export const CosmicBackground: React.FC<CosmicBackgroundProps> = ({
  variant = 'dashboard',
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Generate star field layers
    const starCount = variant === 'landing' ? 180 : variant === 'dashboard' ? 120 : 70;
    const stars: Array<{
      x: number;
      y: number;
      radius: number;
      alpha: number;
      baseAlpha: number;
      speed: number;
      color: string;
      pulsePhase: number;
    }> = [];

    const starColors = ['#FFFFFF', '#D8D3E2', '#9B7FD4', '#8FD3FF', '#55C7D9', '#D6A84F'];

    for (let i = 0; i < starCount; i++) {
      const radius = Math.random() < 0.8 ? Math.random() * 0.9 + 0.3 : Math.random() * 1.2 + 0.8;
      const alpha = Math.random() * 0.65 + 0.2;
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius,
        alpha,
        baseAlpha: alpha,
        speed: Math.random() * 0.05 + 0.01,
        color: starColors[Math.floor(Math.random() * starColors.length)],
        pulsePhase: Math.random() * Math.PI * 2
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw Stars
      for (let i = 0; i < stars.length; i++) {
        const star = stars[i];

        if (!prefersReducedMotion) {
          star.pulsePhase += star.speed * 0.5;
          star.alpha = star.baseAlpha + Math.sin(star.pulsePhase) * 0.2;
          star.alpha = Math.max(0.1, Math.min(0.9, star.alpha));
        }

        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fillStyle = star.color;
        ctx.globalAlpha = star.alpha;
        ctx.fill();
      }

      ctx.globalAlpha = 1.0;

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [variant]);

  const opacityClass =
    variant === 'landing' ? 'opacity-85' : variant === 'dashboard' ? 'opacity-60' : 'opacity-40';

  return (
    <div className={`fixed inset-0 pointer-events-none overflow-hidden z-0 ${className}`}>
      {/* Deep Purple Galaxy Base Foundation */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#03040A] via-[#0D0A1C] to-[#070912]" />

      {/* Atmospheric Purple & Indigo Galaxy Nebula Layers */}
      <div
        className={`absolute -top-10 right-1/4 w-[750px] h-[550px] rounded-full blur-[150px] bg-gradient-to-br from-[#21133B]/45 via-[#15102A]/35 to-transparent transition-opacity duration-1000 ${opacityClass}`}
      />
      <div
        className={`absolute bottom-10 left-10 w-[700px] h-[480px] rounded-full blur-[160px] bg-gradient-to-tr from-[#181536]/50 via-[#7657B8]/10 to-transparent transition-opacity duration-1000 ${opacityClass}`}
      />
      <div
        className={`absolute top-1/3 left-1/2 -translate-x-1/2 w-[900px] h-[600px] rounded-full blur-[190px] bg-gradient-to-r from-[#9B7FD4]/06 via-[#526AA8]/05 to-[#21133B]/25 transition-opacity duration-1000 ${opacityClass}`}
      />

      {/* Dynamic Starfield Canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />

      {/* Grid Scanline Overlay */}
      <div className="absolute inset-0 scanline-overlay opacity-10 pointer-events-none" />
    </div>
  );
};

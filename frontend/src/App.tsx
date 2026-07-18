import { useRef, useEffect, useState } from "react";
import { SkyChart } from "./components/SkyChart";
import { fetchSkyData } from "./api/client";
import type { SkyData } from "./types";

export default function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [skyData, setSkyData] = useState<SkyData | null>(null);

  useEffect(() => {
    fetchSkyData("부산 가야동", "1995-01-15 06:00", "ko").then(setSkyData);
  }, []);

  if (!skyData) return <div>loading...</div>;
  return <SkyChart skyData={skyData} canvasRef={canvasRef} />;
}

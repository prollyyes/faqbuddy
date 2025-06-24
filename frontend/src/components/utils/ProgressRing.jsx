import React from "react";
import {
  CircularProgressbar,
  buildStyles
} from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";

export default function ProgressRing({ current, total, type = "livello"}) {
  const percentage = (current / total) * 100;

  return (
    <div className="relative w-25 h-25">
      <CircularProgressbar
        value={percentage}
        text={""}
        styles={buildStyles({
          pathColor: "#822433",
          trailColor: "#e8e8e8",
        })}
      />
      <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-[#822433] text-center px-2">
        {`${type.charAt(0).toUpperCase() + type.slice(1)} ${current}/${total}`}
      </div>
    </div>
  );
}
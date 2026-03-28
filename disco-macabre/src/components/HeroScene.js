import dynamic from "next/dynamic";

const HeroScene = dynamic(() => import("./HeroSceneInner"), {
  ssr: false,
  loading: () => (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0a0a0f",
        color: "#58E6D9",
        fontFamily: "var(--font-mont), sans-serif",
        fontSize: "0.875rem",
        letterSpacing: "0.1em",
      }}
    >
      Loading...
    </div>
  ),
});

export default HeroScene;

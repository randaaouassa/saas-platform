import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";

// Fix default marker icons broken by bundlers
const defaultIcon = L.icon({
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    iconRetinaUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

export interface MapPoint {
    id: string;
    lat: number;
    lng: number;
    label?: string;
    color?: "purple" | "green" | "blue" | "red";
}

export interface MapLine {
    points: [number, number][];
    color?: string;
}

interface Props {
    center?: [number, number];
    zoom?: number;
    points?: MapPoint[];
    lines?: MapLine[];
    height?: number;
}

const COLOR_HEX: Record<string, string> = {
    purple: "#a855f7",
    green: "#34d399",
    blue: "#60a5fa",
    red: "#f87171",
};

function coloredIcon(color: string) {
    return L.divIcon({
        className: "",
        html: `<div style="
      width: 18px; height: 18px; border-radius: 999px;
      background: ${color}; border: 2px solid rgba(255,255,255,0.8);
      box-shadow: 0 0 12px ${color};
    "></div>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
    });
}

export default function Map({
    center = [0, 0],
    zoom = 11,
    points = [],
    lines = [],
    height = 300,
}: Props) {
    return (
        <div
            style={{ height }}
            className="rounded-2xl overflow-hidden border border-white/10"
        >
            <MapContainer
                center={center}
                zoom={zoom}
                style={{ height: "100%", width: "100%" }}
                scrollWheelZoom={false}
            >
                <TileLayer
                    attribution='&copy; OpenStreetMap contributors'
                    url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {lines.map((l, i) => (
                    <Polyline
                        key={i}
                        positions={l.points}
                        pathOptions={{ color: l.color ?? "#a855f7", weight: 3 }}
                    />
                ))}
                {points.map((p) => (
                    <Marker
                        key={p.id}
                        position={[p.lat, p.lng]}
                        icon={coloredIcon(COLOR_HEX[p.color ?? "purple"])}
                    >
                        {p.label && <Popup>{p.label}</Popup>}
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
}
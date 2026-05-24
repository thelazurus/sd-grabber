import io
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone


def _sd_dt_to_xmltv(dt_str: str) -> str:
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.strftime("%Y%m%d%H%M%S +0000")


def _end_time(start_str: str, duration_secs: int) -> str:
    dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    return (dt + timedelta(seconds=duration_secs)).strftime("%Y%m%d%H%M%S +0000")


def build_xmltv(
    stations: list[dict],
    schedules: list[dict],
    programs: dict[str, dict],
) -> bytes:
    root = ET.Element("tv", attrib={"generator-info-name": "sd-grabber"})

    for station in stations:
        sid = station["stationID"]
        ch = ET.SubElement(root, "channel", id=sid)

        name = station.get("name") or station.get("callsign", sid)
        ET.SubElement(ch, "display-name").text = name

        callsign = station.get("callsign", "")
        if callsign and callsign != name:
            ET.SubElement(ch, "display-name").text = callsign

        if logo_url := station.get("logo", {}).get("URL"):
            ET.SubElement(ch, "icon", src=logo_url)

    for sched in schedules:
        sid = sched["stationID"]
        for airing in sched.get("programs", []):
            prog_id = airing["programID"]
            prog_data = programs.get(prog_id, {})

            start = _sd_dt_to_xmltv(airing["airDateTime"])
            stop = _end_time(airing["airDateTime"], airing.get("duration", 0))

            prog = ET.SubElement(root, "programme", start=start, stop=stop, channel=sid)

            titles = prog_data.get("titles", [])
            title_text = next(
                (t.get("title120") for t in titles if t.get("title120")),
                prog_id,
            )
            ET.SubElement(prog, "title", lang="en").text = title_text

            if ep_title := prog_data.get("episodeTitle150"):
                ET.SubElement(prog, "sub-title", lang="en").text = ep_title

            descs = prog_data.get("descriptions", {})
            desc_text = None
            for key in ("description1000", "description100"):
                items = descs.get(key, [])
                if items:
                    desc_text = items[0].get("description")
                    break
            if desc_text:
                ET.SubElement(prog, "desc", lang="en").text = desc_text

            for genre in prog_data.get("genres", []):
                ET.SubElement(prog, "category", lang="en").text = genre

            for meta in prog_data.get("metadata", []):
                gn = meta.get("Gracenote", {})
                season = gn.get("season")
                episode = gn.get("episode")
                if season and episode:
                    ET.SubElement(prog, "episode-num", system="xmltv_ns").text = (
                        f"{season - 1}.{episode - 1}."
                    )
                    break

            ET.SubElement(prog, "episode-num", system="dd_progid").text = prog_id

            if airing.get("new"):
                ET.SubElement(prog, "new")

            if orig := prog_data.get("originalAirDate"):
                ET.SubElement(prog, "date").text = orig.replace("-", "")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    buf = io.BytesIO()
    tree.write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()

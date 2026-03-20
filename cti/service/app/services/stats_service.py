from sqlalchemy.orm import Session

from ..repositories.indicator_repository import IndicatorRepository


def get_stats(db: Session) -> dict:
    repo = IndicatorRepository

    suricata_indicators = repo.count_by_source(db, "suricata")
    suricata_sightings = repo.count_sightings_by_source(db, "suricata")
    wazuh_indicators = repo.count_by_source(db, "wazuh")
    wazuh_sightings = repo.count_sightings_by_source(db, "wazuh")
    cape_indicators = repo.count_by_source(db, "cape")
    malware_families = repo.count_malware(db)
    total_indicators = repo.count_all_indicators(db)
    total_sightings = repo.count_all_sightings(db)
    total_attack_patterns = repo.count_attack_patterns(db)

    return {
        "suricata": {
            "indicators": suricata_indicators,
            "sightings": suricata_sightings,
        },
        "wazuh": {
            "indicators": wazuh_indicators,
            "sightings": wazuh_sightings,
        },
        "cape": {
            "indicators": cape_indicators,
            "malware_families": malware_families,
        },
        "totals": {
            "indicators": total_indicators,
            "sightings": total_sightings,
            "malware_families": malware_families,
            "attack_patterns": total_attack_patterns,
        },
    }

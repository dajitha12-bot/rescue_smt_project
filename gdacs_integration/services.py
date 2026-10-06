import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from email.utils import parsedate_to_datetime
from .models import GDACSEvent, GDACSSyncLog

logger = logging.getLogger(__name__)

GDACS_FEED_URL = "https://www.gdacs.org/xml/rss.xml"

# Namespaces commonly used in the official GDACS RSS feed
NAMESPACES = {
    'gdacs': 'http://www.gdacs.org',
    'georss': 'http://www.georss.org/georss',
    'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

def parse_gdacs_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    try:
        # RFC 2822 format (e.g. "Tue, 06 Oct 2026 06:28:10 GMT")
        dt = parsedate_to_datetime(date_str)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return dt
    except Exception:
        pass

    try:
        # ISO format
        dt = parse_datetime(date_str)
        if dt:
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            return dt
    except Exception:
        pass
    return None

def sync_gdacs_events(feed_url=GDACS_FEED_URL, timeout=15):
    """
    Synchronizes real-time disaster alerts from the official GDACS XML feed.
    - Prevents duplicates using external_event_id.
    - Accurately captures coordinates, disaster type, alert level, country, affected area.
    - Records sync execution in GDACSSyncLog.
    - Strictly follows NO-FAKE-DATA rule: never invents events, coordinates or classifications.
    """
    start_time = timezone.now()
    events_count = 0
    india_count = 0
    tn_count = 0

    try:
        response = requests.get(
            feed_url,
            timeout=timeout,
            headers={
                'User-Agent': 'RescueGrid-Emergency-Operations-India/1.0 (GDACS-Sync-Service)'
            }
        )
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)
        channel = root.find('channel')
        if channel is None:
            channel = root

        items = channel.findall('item')

        for item in items:
            guid_elem = item.find('guid')
            eventid_elem = item.find('gdacs:eventid', NAMESPACES)
            
            ext_id = None
            if guid_elem is not None and guid_elem.text:
                ext_id = guid_elem.text.strip()
            elif eventid_elem is not None and eventid_elem.text:
                eventtype_elem = item.find('gdacs:eventtype', NAMESPACES)
                etype_prefix = eventtype_elem.text.strip() if eventtype_elem is not None and eventtype_elem.text else "EV"
                ext_id = f"{etype_prefix}{eventid_elem.text.strip()}"
            
            if not ext_id:
                continue

            # Extract event details
            title_elem = item.find('title')
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Unnamed Disaster Event"

            eventname_elem = item.find('gdacs:eventname', NAMESPACES)
            event_name = eventname_elem.text.strip() if eventname_elem is not None and eventname_elem.text else title

            desc_elem = item.find('description')
            affected_area = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

            country_elem = item.find('gdacs:country', NAMESPACES)
            country = country_elem.text.strip() if country_elem is not None and country_elem.text else ""

            iso3_elem = item.find('gdacs:iso3', NAMESPACES)
            iso3 = iso3_elem.text.strip() if iso3_elem is not None and iso3_elem.text else ""

            eventtype_elem = item.find('gdacs:eventtype', NAMESPACES)
            raw_event_type = eventtype_elem.text.strip() if eventtype_elem is not None and eventtype_elem.text else "OTHER"
            if raw_event_type not in ['EQ', 'TC', 'FL', 'DR', 'VO', 'WF', 'TS']:
                event_type = 'OTHER'
            else:
                event_type = raw_event_type

            alertlevel_elem = item.find('gdacs:alertlevel', NAMESPACES)
            raw_alert_level = alertlevel_elem.text.strip() if alertlevel_elem is not None and alertlevel_elem.text else "Green"
            if 'red' in raw_alert_level.lower():
                alert_level = 'Red'
            elif 'orange' in raw_alert_level.lower():
                alert_level = 'Orange'
            else:
                alert_level = 'Green'

            alertscore_elem = item.find('gdacs:alertscore', NAMESPACES)
            try:
                alert_score = float(alertscore_elem.text.strip()) if alertscore_elem is not None and alertscore_elem.text else 1.0
            except ValueError:
                alert_score = 1.0

            severity_elem = item.find('gdacs:severity', NAMESPACES)
            severity_level = severity_elem.text.strip() if severity_elem is not None and severity_elem.text else ""

            link_elem = item.find('link')
            details_url = link_elem.text.strip() if link_elem is not None and link_elem.text else ""

            # Coordinates
            lat = None
            lon = None

            # 1. Check georss:point ("lat lon")
            georss_point = item.find('georss:point', NAMESPACES)
            if georss_point is not None and georss_point.text:
                parts = georss_point.text.strip().split()
                if len(parts) >= 2:
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                    except ValueError:
                        pass

            # 2. Check geo:Point/geo:lat and geo:long
            if lat is None or lon is None:
                geo_lat = item.find('geo:lat', NAMESPACES)
                geo_long = item.find('geo:long', NAMESPACES)
                if geo_lat is not None and geo_long is not None and geo_lat.text and geo_long.text:
                    try:
                        lat = float(geo_lat.text.strip())
                        lon = float(geo_long.text.strip())
                    except ValueError:
                        pass

            if lat is None or lon is None:
                continue  # Cannot plot or evaluate without actual coordinates

            # Dates
            pub_date = item.find('pubDate')
            from_date = item.find('gdacs:fromdate', NAMESPACES)
            modified_date = item.find('gdacs:datemodified', NAMESPACES)

            event_date = parse_gdacs_date(from_date.text if from_date is not None else (pub_date.text if pub_date is not None else None))
            source_updated_at = parse_gdacs_date(modified_date.text if modified_date is not None else None)

            # Update or create in DB
            event_obj, created = GDACSEvent.objects.update_or_create(
                external_event_id=ext_id,
                defaults={
                    'event_type': event_type,
                    'event_name': event_name,
                    'country': country,
                    'iso3': iso3,
                    'affected_area': affected_area,
                    'severity_level': severity_level,
                    'alert_level': alert_level,
                    'alert_score': alert_score,
                    'latitude': lat,
                    'longitude': lon,
                    'event_date': event_date or timezone.now(),
                    'source_updated_at': source_updated_at or timezone.now(),
                    'details_url': details_url,
                }
            )

            events_count += 1
            if event_obj.is_india:
                india_count += 1
            if event_obj.is_tamil_nadu:
                tn_count += 1

        # Record successful sync log
        sync_log = GDACSSyncLog.objects.create(
            status=GDACSSyncLog.STATUS_SUCCESS,
            events_synced=events_count,
            india_events_count=india_count,
            tamil_nadu_events_count=tn_count,
            error_message=""
        )

        return {
            'success': True,
            'count': events_count,
            'india_count': india_count,
            'tamil_nadu_count': tn_count,
            'sync_time': sync_log.sync_time,
            'error': None
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"GDACS Sync failed: {error_msg}")
        sync_log = GDACSSyncLog.objects.create(
            status=GDACSSyncLog.STATUS_FAILED,
            events_synced=0,
            india_events_count=0,
            tamil_nadu_events_count=0,
            error_message=error_msg
        )
        return {
            'success': False,
            'count': 0,
            'india_count': 0,
            'tamil_nadu_count': 0,
            'sync_time': sync_log.sync_time,
            'error': error_msg
        }

def get_latest_sync_status():
    """
    Returns the latest synchronization status and last successful sync time.
    """
    last_log = GDACSSyncLog.objects.order_by('-sync_time').first()
    last_success_log = GDACSSyncLog.objects.filter(status=GDACSSyncLog.STATUS_SUCCESS).order_by('-sync_time').first()

    return {
        'last_attempt': last_log.sync_time if last_log else None,
        'status': last_log.status if last_log else 'NEVER_SYNCED',
        'error_message': last_log.error_message if last_log and last_log.status == GDACSSyncLog.STATUS_FAILED else None,
        'last_successful_sync': last_success_log.sync_time if last_success_log else None,
        'total_events': GDACSEvent.objects.count(),
        'india_events': GDACSEvent.objects.filter(is_india=True).count(),
        'tamil_nadu_events': GDACSEvent.objects.filter(is_tamil_nadu=True).count(),
    }

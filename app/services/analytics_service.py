from app.models import ClickEvent


class AnalyticsService:
    def __init__(self, link_service):
        self._link_service = link_service

    def get_link_analytics(self, user, link_id):
        link = self._link_service.get_owned_link(user, link_id)
        events = ClickEvent.query.filter_by(link_id=link.id).all()

        device_breakdown = self._count_by(events, "device_type", "unknown")
        browser_breakdown = self._count_by(events, "browser", "unknown")
        referrer_breakdown = self._count_by(events, "referrer_domain", "direct")
        top_referrers = self._top_counts(referrer_breakdown, 5)

        return {
            "link_id": link.id,
            "code": link.code,
            "total_clicks": link.click_count,
            "processed_events": len(events),
            "device_breakdown": device_breakdown,
            "browser_breakdown": browser_breakdown,
            "top_referrers": top_referrers,
        }

    @staticmethod
    def _count_by(events, field_name, default_value):
        counts = {}
        for event in events:
            value = getattr(event, field_name) or default_value
            if value in counts:
                counts[value] += 1
            else:
                counts[value] = 1
        return counts

    @staticmethod
    def _top_counts(counts, limit):
        pairs = list(counts.items())
        pairs.sort(key=lambda pair: pair[1], reverse=True)
        return pairs[:limit]

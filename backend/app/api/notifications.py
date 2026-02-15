"""
Notification API endpoints
"""
from flask import Blueprint, request, jsonify
from app.notifications.manager import NotificationManager
import logging

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/test', methods=['POST'])
def test_notification():
    """
    Test notification channel

    POST /api/v1/notifications/test
    {
        "channel": "email-admin"  // optional, tests all if not specified
    }
    """
    try:
        data = request.get_json() or {}
        channel_name = data.get('channel')

        manager = NotificationManager()

        if channel_name:
            # Test specific channel
            success = manager.test_channel(channel_name)
            return jsonify({
                'success': success,
                'channel': channel_name,
                'message': 'Test notification sent' if success else 'Failed to send test notification'
            }), 200 if success else 500
        else:
            # Test all channels
            results = manager.notify(
                title="🧪 Test Notification",
                message="This is a test notification from BackupGenie. Your notification system is working correctly!",
            )

            return jsonify({
                'success': any(results.values()),
                'results': results,
                'message': f"Test sent to {len(results)} channel(s)"
            }), 200

    except Exception as e:
        logger.error(f"Error testing notification: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/channels', methods=['GET'])
def list_channels():
    """
    List all configured notification channels

    GET /api/v1/notifications/channels
    """
    try:
        manager = NotificationManager()
        channels = manager.get_enabled_channels()

        return jsonify({
            'channels': channels,
            'count': len(channels)
        }), 200

    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        return jsonify({'error': str(e)}), 500


@notifications_bp.route('/send', methods=['POST'])
def send_notification():
    """
    Send custom notification

    POST /api/v1/notifications/send
    {
        "title": "Custom Notification",
        "message": "Your custom message",
        "priority": "normal",  // low, normal, high, urgent
        "channels": ["email-admin"]  // optional
    }
    """
    try:
        data = request.get_json()

        if not data or not data.get('title') or not data.get('message'):
            return jsonify({'error': 'Title and message are required'}), 400

        title = data['title']
        message = data['message']
        priority_str = data.get('priority', 'normal')
        channels = data.get('channels')

        # Map priority string to enum
        from app.notifications.base import NotificationPriority, NotificationType
        priority_map = {
            'low': NotificationPriority.LOW,
            'normal': NotificationPriority.NORMAL,
            'high': NotificationPriority.HIGH,
            'urgent': NotificationPriority.URGENT,
        }
        priority = priority_map.get(priority_str.lower(), NotificationPriority.NORMAL)

        manager = NotificationManager()
        results = manager.notify(
            title=title,
            message=message,
            priority=priority,
            notification_type=NotificationType.SYSTEM_WARNING,
            channels=channels
        )

        return jsonify({
            'success': any(results.values()),
            'results': results,
            'message': f"Notification sent to {sum(1 for r in results.values() if r)}/{len(results)} channel(s)"
        }), 200

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return jsonify({'error': str(e)}), 500

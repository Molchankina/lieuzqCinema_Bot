import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from bot.database import get_session
from bot.movie_api import movie_api

logger = logging.getLogger(__name__)

class ReminderManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def check_new_episodes(self, context):
        """Проверка новых серий (упрощенная версия для КиноПоиска)"""
        session = get_session()
        try:
            from bot.database import TVSeriesReminder
            reminders = session.query(TVSeriesReminder).filter_by(is_active=True).all()

            for reminder in reminders:
                await self._check_series(reminder, context, session)

        except Exception as e:
            logger.error(f"Ошибка при проверке новых серий: {e}")
        finally:
            session.close()

    async def _check_series(self, reminder, context, session):
        """Проверка конкретного сериала"""
        try:
            # Получаем информацию о сериале
            details = movie_api.get_details(reminder.series_id)

            if not details:
                return

            # Для КиноПоиска нет точных дат выхода серий
            # Можно проверять изменения в данных
            last_updated = details.get('last_sync')

            if last_updated:
                last_updated_dt = datetime.strptime(last_updated, '%Y-%m-%dT%H:%M:%S')
                if reminder.updated_at and last_updated_dt > reminder.updated_at:
                    # Обновляем время проверки
                    reminder.updated_at = datetime.utcnow()
                    session.commit()

                    # Уведомляем пользователя
                    await self._notify_user(reminder, context, details)

        except Exception as e:
            logger.error(f"Ошибка проверки сериала {reminder.series_id}: {e}")

    async def _notify_user(self, reminder, context, details):
        """Уведомление пользователя"""
        try:
            message = f"🎬 Обновление по сериалу *{reminder.series_name}*\n\n"

            # Добавляем информацию об обновлении
            if details.get('seasons'):
                seasons = details['seasons']
                if seasons:
                    last_season = seasons[-1]
                    message += f"Сезон {last_season.get('number')}: {last_season.get('episodes', [])} эпизодов\n"

            message += "\nХочешь посмотреть что-нибудь новенькое? 😊"

            await context.bot.send_message(
                chat_id=reminder.user_id,
                text=message,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

# Глобальный экземпляр
reminder_manager = ReminderManager()
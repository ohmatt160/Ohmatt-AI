from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.tasks import router as tasks_router
from app.routes.geo import router as geo_router
from app.routes.transactions import router as transactions_router
from app.routes.messages import router as messages_router
from app.routes.bank import router as bank_router
from app.routes.admin import router as admin_router
from app.routes.messages import router as messages_router
from app.routes.tasks import router as tasks_router
from app.routes.geo import router as geo_router
from app.routes.transactions import router as transactions_router
from app.routes.auth import router as auth_router
from app.routes.webhooks import router as webhooks_router
from app.routes.users import router as users_router
from app.routes.finance import router as finance_router
from app.routes.activity import router as activity_router
from app.routes.ai import router as ai_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(tasks_router)
api_router.include_router(geo_router)
api_router.include_router(transactions_router)
api_router.include_router(messages_router)
api_router.include_router(bank_router)
api_router.include_router(admin_router)
api_router.include_router(webhooks_router)
api_router.include_router(users_router)
api_router.include_router(finance_router)
api_router.include_router(activity_router)
api_router.include_router(ai_router)

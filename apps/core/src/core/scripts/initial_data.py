import asyncio
import logging

import core._dotenv  # noqa: E402, F401, I001
from core.core.config import settings
from core.db.models.folder import Folder
from core.db.models.layer import Layer
from core.db.models.user import User
from core.db.session import session_manager
from core.db.sql.init_functions import init_functions
from core.db.sql.init_triggers import init_triggers
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("initial_data")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

admin_user_id = "744e4fd1-685c-495c-8b02-efebce875359"


async def create_default_users(session: AsyncSession) -> None:
    """Create default admin user and home folder if not exist."""
    result = await session.execute(select(User).where(User.id == admin_user_id))
    user = result.scalar_one_or_none()
    if user:
        logger.info("Admin user already exists, skipping user creation...")
    else:
        user = User(
            id=admin_user_id,
            firstname="Local",
            lastname="User",
            avatar="https://assets.plan4better.de/img/no-user-thumb.jpg",
        )
        session.add(user)
        logger.info("Created default admin user.")

    await session.commit()


async def create_base_network_layers(session: AsyncSession) -> None:
    """Create base network layers if not exist."""
    # Placeholder for actual implementation
    logger.info("Base network layers creation is not implemented yet.")
    result = await session.execute(
        select(Layer).where(Layer.id == settings.BASE_STREET_NETWORK)
    )
    layer = result.scalar_one_or_none()
    if layer:
        logger.info("Base street network layer already exists, skipping creation...")
        return
    else:
        logger.info("Creating base street network layer...")
        folder_result = await session.execute(
            select(Folder).where(Folder.name == "home", Folder.user_id == admin_user_id)
        )
        folder = folder_result.scalar_one_or_none()
        if not folder:
            logger.error(
                "Home folder for admin user does not exist, cannot create base street network layer."
            )
            return

        layer = Layer(
            id=settings.BASE_STREET_NETWORK,
            name="Street Network - Edges",
            thumbnail_url=settings.DEFAULT_LAYER_THUMBNAIL,
            type="feature",
            user_id=admin_user_id,
            folder_id=folder.id,
            feature_layer_type="street_network",
            feature_layer_geometry_type="line",
            extent="MULTIPOLYGON(((-180 -90, -180 90, 180 90, 180 -90, -180 -90)))",
            size=3800,
            attribute_mapping={
                "text_attr1": "bicycle",
                "text_attr2": "foot",
                "text_attr3": "class_",
                "float_attr1": "length_m",
                "float_attr2": "length_3857",
                "float_attr3": "impedance_slope",
                "float_attr4": "impedance_slope_reverse",
                "float_attr5": "impedance_surface",
                "integer_attr1": "maxspeed_forward",
                "integer_attr2": "maxspeed_backward",
            },
            properties={
                "color": [50, 136, 189],
                "filled": True,
                "opacity": 1,
                "stroked": True,
                "max_zoom": 22,
                "min_zoom": 1,
                "visibility": True,
                "stroke_color": [50, 136, 189],
                "stroke_width": 7,
                "stroke_width_range": [0, 10],
                "stroke_width_scale": "linear",
            },
        )
        session.add(layer)
        logger.info("Created base street network layer.")
    # Here you would add the logic to create the layers
    await session.commit()


async def init_basic_data() -> None:
    """Run all initial data seeds."""
    async with session_manager.session() as session:
        await create_default_users(session)
        await create_base_network_layers(session)
        # Add more seed functions here


async def main() -> None:
    logger.info("Starting initial data seeding...")
    session_manager.init(settings.ASYNC_SQLALCHEMY_DATABASE_URI)
    try:
        await init_functions()
        await init_triggers()
        await init_basic_data()
        logger.info("Seeding completed successfully.")
    finally:
        await session_manager.close()


if __name__ == "__main__":
    asyncio.run(main())

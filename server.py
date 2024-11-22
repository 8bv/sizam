import logging
import sys

import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sizam.config import load_config
from sizam.views.main import create_app

logger = logging.getLogger(__name__)


def main(config_path):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    config = load_config(config_path)
    engine = create_engine(config.db.sqla_url)
    session_maker = sessionmaker(engine)

    logger.warning("Prog started")
    app = create_app(session_maker, config.wiki2035.platform_id)

    uvicorn.run(app, host=config.uvicorn.host, port=config.uvicorn.port)


if __name__ == "__main__":
    main(sys.argv[1])

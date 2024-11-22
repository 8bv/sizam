import logging
import sys

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sizam.config import load_config
from sizam.sevices import RequestMakerService

logger = logging.getLogger(__name__)


def main(config_path):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    config = load_config(config_path)
    engine = create_engine(config.db.sqla_url)
    session_maker = sessionmaker(engine)

    logger.warning("Prog started")
    with (
        httpx.Client(base_url=config.wiki2035.base_url, timeout=httpx.Timeout(10, write=20)) as client
    ):
        client.headers["Authorization"] = config.wiki2035.token
        requests_maker = RequestMakerService(session_maker(), client)
        requests_maker.run()


if __name__ == "__main__":
    main(sys.argv[1])

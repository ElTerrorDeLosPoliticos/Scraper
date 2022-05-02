from Presidencia.runner_scraper import Presidencia
from Congreso.runner_scraper import Congreso
import argparse
import logging


def run_presidencia():
    """[Runner of Despacho Presidencial scrapper]

    Returns:
        [bool]: If correct, return True
    """
    x = Presidencia()
    x.compute()
    return True

def run_congreso():
    """[Runner of Congreso scrapper]

    Returns:
        [Bool]: If correct, return True
    """
    x = Congreso()
    x.compute()
    return True
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Choose your fighter(presidencia|congreso)')
    parser.add_argument("poder", help="presidencia|congreso", type=str, choices=['presidencia', 'congreso'])

    args = parser.parse_args()
    
    if (args.poder) == "presidencia":
        run_presidencia()
    elif (args.poder) == "congreso":
        run_congreso()
    else:
        pass

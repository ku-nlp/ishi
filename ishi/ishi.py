"""Ishi: A volition classifier for Japanese."""
from logging import getLogger, StreamHandler, Formatter
import re
import os
import typing

from pyknp import KNP
from mojimoji import han_to_zen


here = os.path.dirname(os.path.abspath(__file__))


def is_volition(input_str, logging_level='INFO'):
    """Checks if the given input has volition.

    Args:
        input_str (str): An input string.
        logging_level (str): The logging level.

    Returns:
        bool: True for having volition, False otherwise.
    """
    ishi = Ishi()
    return ishi(input_str, logging_level)


def get_exceptional_head_repnames():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'exceptional_head_repnames.txt')) as f:
        return [line.strip() for line in f]


class Ishi:
    """Ishi is a volition classifier for Japanese."""

    def __init__(self, exceptional_head_repnames=None):
        """Ishi prepares KNP and a list of exceptional head repnames.

        Args:
            exceptional_head_repnames (typing.List[str]): A list of exceptional head repnames.
                Ishi judges that clauses with these head repnames do not have volition.
        """
        self.logger = getLogger(__name__)
        handler = StreamHandler()
        handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

        self.knp = KNP()

        if exceptional_head_repnames:
            self.exceptional_head_repnames = set(exceptional_head_repnames)
        else:
            self.exceptional_head_repnames = set(get_exceptional_head_repnames())

    def __call__(self, input_str, logging_level='INFO'):
        """Checks if the given input has volition.

        Ishi relies on language analysis by Jumanpp.

        Args:
            input_str (str): An input string.
            logging_level (str): The logging level.

        Returns:
            bool: True for having volition, False otherwise.
        """
        self.logger.setLevel(logging_level)

        self.logger.debug(f'Input string: {input_str}')

        preprocessed = self.preprocess_input_str(input_str)
        knp_output = self.knp.parse(preprocessed)
        for tag in reversed(knp_output.tag_list()):
            # find the last predicate
            predicate_type = re.search('<用言:([動形判])>', tag.fstring)

            if predicate_type:
                # checks the type of the predicate
                if predicate_type.group(1) in ('形', '判'):
                    self.logger.debug(f'No volition: the predicate is {predicate_type.group(1)}')
                    return False

                # check if the predicate is exceptional
                if (tag.head_prime_repname or tag.head_repname) in self.exceptional_head_repnames:
                    self.logger.debug(f'No volition: this predicate is exceptional')
                    return False

                # checks the feature of the predicate
                for mrph in tag.mrph_list():
                    # 可能動詞: 飲める, 走れる
                    if '可能動詞' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 可能動詞')
                        return False

                    # 自他動詞:他: 色づく, 削れる
                    if '自他動詞:他' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 自他動詞:他')
                        return False

                    # 可能接尾辞: 預けておける, 持っていける
                    if '可能接尾辞' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 可能接尾辞')
                        return False

                    # 動詞性接尾辞:なる: おいしくなくなる
                    if 'なる' == mrph.genkei and '動詞性接尾辞' == mrph.bunrui:
                        self.logger.debug(f'No volition: {mrph.midasi} is 動詞性接尾辞:なる')
                        return False

                return True

        return False

    @staticmethod
    def preprocess_input_str(input_str):
        """Modifies the given input so that Jumanpp can analyze it.

        Args:
            input_str (str): An input string.

        Returns:
            str: The preprocessed string.
        """
        preprocessed = han_to_zen(input_str)
        return preprocessed

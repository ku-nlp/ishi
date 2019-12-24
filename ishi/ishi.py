"""Ishi: A volition classifier for Japanese."""
from logging import getLogger, StreamHandler, Formatter
import re
import os
import typing

from pyknp import KNP, BList
from mojimoji import han_to_zen


here = os.path.dirname(os.path.abspath(__file__))


def has_volition(str_or_blist, logging_level='INFO'):
    """Checks if the given input has volition.

    Args:
        str_or_blist (typing.Union[str, BList]): An input string or the language analysis by KNP.
        logging_level (str): The logging level.

    Returns:
        bool: True for having volition, False otherwise.

    """
    ishi = Ishi()
    return ishi(str_or_blist, logging_level)


def get_exceptional_head_repnames():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'no_volition_head_repnames.txt')) as f:
        return [line.strip() for line in f]


class Ishi:
    """Ishi is a volition classifier for Japanese."""

    def __init__(self, no_volition_head_repnames=None):
        """Ishi prepares KNP and a list of exceptional head repnames.

        Args:
            no_volition_head_repnames (typing.List[str]): A list of exceptional head repnames.
                Ishi judges that clauses with these head repnames do not have volition.

        """
        self.logger = getLogger(__name__)
        handler = StreamHandler()
        handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

        self.knp = KNP()

        if no_volition_head_repnames:
            self.exceptional_head_repnames = set(no_volition_head_repnames)
        else:
            self.exceptional_head_repnames = set(get_exceptional_head_repnames())

    def __call__(self, str_or_blist, logging_level='INFO'):
        """Checks if the given input has volition.

        Ishi relies on language analysis by Jumanpp.

        Args:
            str_or_blist (typing.Union[str, BList]): An input string or the language analysis by KNP.
            logging_level (str): The logging level.

        Returns:
            bool: True for having volition, False otherwise.

        """
        self.logger.setLevel(logging_level)

        if isinstance(str_or_blist, str):
            self.logger.debug(f'Input string: {str_or_blist}')
            preprocessed = self.preprocess_input_str(str_or_blist)
            knp_output = self.knp.parse(preprocessed)
        elif isinstance(str_or_blist, BList):
            self.logger.debug(f'Input string: {"".join(m.midasi for m in str_or_blist.mrph_list())}')
            knp_output = str_or_blist
        else:
            raise RuntimeError

        for tag in reversed(knp_output.tag_list()):
            # find the last predicate
            predicate_type = re.search('<用言:([動形判])>', tag.fstring)

            if predicate_type:
                # checks the type of the predicate
                if predicate_type.group(1) in ('形', '判'):
                    self.logger.debug(f'No volition: the predicate is {predicate_type.group(1)}')
                    return False

                # checks the modality of the predicate
                for modality in re.findall("<モダリティ-(.+?)>", tag.fstring):
                    if modality in ('意志',):
                        self.logger.debug(f'No volition: the predicate has the modality of volition')
                        return False

                # check if the predicate is exceptional
                if (tag.head_prime_repname or tag.head_repname) in self.exceptional_head_repnames:
                    self.logger.debug(f'No volition: this predicate is exceptional')
                    return False

                # checks the feature of the predicate
                for mrph in reversed(tag.mrph_list()):
                    # 動詞性接尾辞:なる: おいしくなくなる
                    if 'なる' == mrph.genkei and '動詞性接尾辞' == mrph.bunrui:
                        self.logger.debug(f'No volition: {mrph.midasi} is 動詞性接尾辞:なる')
                        return False

                    # 可能接尾辞: 預けておける, 持っていける
                    if '可能接尾辞' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 可能接尾辞')
                        return False

                    # 可能動詞: 飲める, 走れる
                    if '可能動詞' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 可能動詞')
                        return False

                    # 自他動詞:他: 色づく, 削れる
                    if '自他動詞:他' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 自他動詞:他')
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

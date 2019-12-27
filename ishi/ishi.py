"""Ishi: A volition classifier for Japanese."""
from logging import getLogger, StreamHandler, Formatter
import re
import os
import typing

from pyknp import KNP, BList, Tag
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


def get_non_volition_head_repnames():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'non_volition_head_repnames.txt')) as f:
        return [line.strip() for line in f]


class Ishi:
    """Ishi is a volition classifier for Japanese."""

    def __init__(self, non_volition_head_repnames=None):
        """Ishi prepares KNP and a list of exceptional head repnames.

        Args:
            non_volition_head_repnames (typing.List[str]): A list of exceptional head repnames.
                Ishi judges that clauses with these head repnames do not have volition.

        """
        self.logger = getLogger(__name__)
        handler = StreamHandler()
        handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

        self.knp = KNP()

        if non_volition_head_repnames:
            self.exceptional_head_repnames = set(non_volition_head_repnames)
        else:
            self.exceptional_head_repnames = set(get_non_volition_head_repnames())

    def __call__(self, str_or_blist_or_tag, logging_level='INFO'):
        """Checks if the given input has volition.

        Ishi relies on language analysis by Jumanpp.

        Args:
            str_or_blist_or_tag (typing.Union[str, BList, Tag]): An input string or the language analysis by KNP.
            logging_level (str): The logging level.

        Returns:
            bool: True for having volition, False otherwise.

        """
        self.logger.setLevel(logging_level)

        if isinstance(str_or_blist_or_tag, str):
            self.logger.debug(f'Input string: {str_or_blist_or_tag}')
            predicate_tag = self.extract_predicate_tag(
                self.knp.parse(
                    self.preprocess_input_str(str_or_blist_or_tag)
                )
            )
        elif isinstance(str_or_blist_or_tag, BList):
            self.logger.debug(f'Input string: {"".join(m.midasi for m in str_or_blist_or_tag.mrph_list())}')
            predicate_tag = self.extract_predicate_tag(str_or_blist_or_tag)
        elif isinstance(str_or_blist_or_tag, Tag):
            predicate_tag = str_or_blist_or_tag
        else:
            raise RuntimeError

        # find the last predicate
        predicate_type = re.search('<用言:([動形判])>', predicate_tag.fstring)

        if predicate_type:
            # checks the voice of the predicate
            predicate_voice = re.search('<態:(.+?)>', predicate_tag.fstring)
            if predicate_voice:
                predicate_voice = predicate_voice.group(1)
                # causative voice: 〜にさせる
                if predicate_voice == {'使役'}:
                    self.logger.debug(f'Volition: the predicate uses the voice of {predicate_voice}')
                    return True

                # passive voice: 言われる, 頼まれる
                if predicate_voice in {'受動'}:
                    self.logger.debug(f'No volition: the predicate uses the voice of {predicate_voice}')
                    return False

            # checks the modality of the predicate
            for modality in re.findall("<モダリティ-(.+?)>", predicate_tag.fstring):
                if modality in {'意志'}:
                    self.logger.debug(f'Volition: the predicate has the modality of {modality}')
                    return True

            # checks the suffix of the predicate
            for mrph in reversed(predicate_tag.mrph_list()):
                # 形容詞性名詞接尾辞: 風邪気味だ
                if '形容詞性名詞接尾辞' == mrph.bunrui:
                    self.logger.debug(f'No volition: {mrph.midasi} is 形容詞性名詞接尾辞')
                    return False

                # 形容詞性述語接尾辞: 読みにくい, しやすい
                if '形容詞性述語接尾辞' == mrph.bunrui:
                    self.logger.debug(f'No volition: {mrph.midasi} is 形容詞性述語接尾辞')
                    return False

                # 動詞性接尾辞
                if '動詞性接尾辞' == mrph.bunrui:
                    # 可能接尾辞: 預けておける, 持っていける
                    if '可能接尾辞' in mrph.imis:
                        self.logger.debug(f'No volition: {mrph.midasi} is 可能接尾辞')
                        return False

                    non_volition_suffixes = {
                        'なる/なる',  # 行かなくなる, しなくなる
                        'くれる/くれる',  # 来てくれる, 叱ってくれる
                        'しまう/しまう',  # 飲んでしまう, 言ってしまう
                        '下さる/くださる',  # 来て下さる
                        '得る/える',   # 考え得る
                        '過ぎる/すぎる',  # 行きすぎる
                        'かねる/かねる',  # しかねる
                        'あぐむ/あぐむ',  # 攻めあぐむ
                        'あぐねる/あぐねる',  # 攻めあぐねる
                        'そびれる/そびれる',  # 書きそびれる
                        'めく/めく',  # 罪人めく
                        'ちまう/ちまう',  # 行っちまう
                        'じまう/じまう',  # 読んじまう
                        'やがる/やがる',  # 帰りやがる
                    }
                    if mrph.repname in non_volition_suffixes:
                        self.logger.debug(f'No volition: {mrph.midasi} is 動詞性接尾辞 which does not imply volition')
                        return False

            # checks the type of the predicate
            if predicate_type.group(1) in {'形', '判'}:
                self.logger.debug(f'No volition: the predicate is {predicate_type.group(1)}')
                return False

            # check if the predicate is exceptional
            if (predicate_tag.head_prime_repname or predicate_tag.head_repname) in self.exceptional_head_repnames:
                self.logger.debug(f'No volition: this predicate is exceptional')
                return False

            # checks the predicate
            for mrph in reversed(predicate_tag.mrph_list()):
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

    @staticmethod
    def extract_predicate_tag(knp_output):
        """Extracts the predicate part from the given KNP output.

        Args:
            knp_output (BList): A KNP output.

        Returns:
            Tag

        """
        for tag in reversed(knp_output.tag_list()):
            if '<用言:' in tag.fstring:
                return tag
        else:
            return knp_output.tag_list()[-1]

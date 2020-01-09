"""Ishi: A volition classifier for Japanese."""
from logging import getLogger, StreamHandler, Formatter
import re
import os
import typing

from pyknp import KNP, BList, Tag
from mojimoji import han_to_zen


def has_volition(str_or_blist_or_tag, nominative_str_or_tag=None, logging_level='INFO'):
    """Checks if the given input has volition.

    Args:
        str_or_blist_or_tag (typing.Union[str, BList, Tag]): An input string or the language analysis by KNP.
        nominative_str_or_tag (typing.Union[str, Tag], optional): The string or language analysis of the nominative.
            If the nominative comes from exophora resolution, pass the surface string such as '著者' and '読者'.
            Otherwise, pass the language analysis of the nominative with the type of pyknp.Tag.
        logging_level (str): The logging level.

    Returns:
        bool: True for having volition, False otherwise.

    """
    ishi = Ishi()
    return ishi(str_or_blist_or_tag, nominative_str_or_tag, logging_level)


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

    def __call__(self, str_or_blist_or_tag, nominative_str_or_tag=None, logging_level='INFO'):
        """Checks if the given input has volition.

        Ishi relies on language analysis by Jumanpp.

        Args:
            str_or_blist_or_tag (typing.Union[str, BList, Tag]): An input string or the language analysis by KNP.
            nominative_str_or_tag (typing.Union[str, Tag], optional): The string or language analysis of the nominative.
                If the nominative comes from exophora resolution, pass the surface string such as '著者' and '読者'.
                Otherwise, pass the language analysis of the nominative with the type of pyknp.Tag.
                If this parameter is None, KNP will analyze the nominative. Care must be taken in that KNP just performs
                case analysis so neither exophora and inter-sentential anaphora will not be resolved.
            logging_level (str): The logging level.

        Returns:
            bool: True for having volition, False otherwise.

        """
        self.logger.setLevel(logging_level)

        if isinstance(str_or_blist_or_tag, str):
            blist = self.knp.parse(self.preprocess_input_str(str_or_blist_or_tag))
            predicate_tag = self.extract_predicate_tag(blist)
        elif isinstance(str_or_blist_or_tag, BList):
            blist = str_or_blist_or_tag
            predicate_tag = self.extract_predicate_tag(blist)
        elif isinstance(str_or_blist_or_tag, Tag):
            blist = None
            predicate_tag = str_or_blist_or_tag
        else:
            raise RuntimeError

        # checks the nominative of the predicate
        if not nominative_str_or_tag:
            if predicate_tag.pas:
                nominatives = predicate_tag.pas.arguments.get('ガ', [])
                if nominatives:
                    nominative = nominatives[0]
                    if nominative.tid == -1:
                        nominative_str_or_tag = nominative.midasi
                    elif blist and nominative.sid == blist.sid and nominative.tid < len(blist.tag_list()):
                        nominative_str_or_tag = blist.tag_list()[nominative.tid]

        if isinstance(nominative_str_or_tag, str):
            if nominative_str_or_tag not in {'著者', '読者', '不特定:人'}:
                self.logger.debug('No volition: the nominative is not a subject')
                return False
        elif isinstance(nominative_str_or_tag, Tag):
            if '主体' not in re.findall("<SM-(.+?)>", nominative_str_or_tag.fstring):
                self.logger.debug('No volition: the nominative is not a subject')
                return False
        else:
            self.logger.warning('Failed to ensure that nominative is a subject')

        # checks the modality
        for modality in re.findall("<モダリティ-(.+?)>", predicate_tag.fstring):
            if modality in {'意志', '命令', '依頼Ａ', '依頼Ｂ', '評価:弱', '評価:強'}:
                self.logger.debug(f'Volition: the predicate has the modality of {modality}')
                return True

        # checks the voice
        predicate_voice = re.search('<態:(.+?)>', predicate_tag.fstring)
        if predicate_voice:
            predicate_voice = predicate_voice.group(1)
            if predicate_voice == '使役':
                self.logger.debug(f'Volition: the predicate uses the voice of {predicate_voice}')
                return True

            if predicate_voice in {'受動', '可能', '受動|可能', '使役&受動', '使役&受動|使役&可能'}:
                self.logger.debug(f'No volition: the predicate uses the voice of {predicate_voice}')
                return False

        # checks the suffix
        for mrph in reversed(predicate_tag.mrph_list()):
            # 形容詞性名詞接尾辞: 風邪気味だ
            if '形容詞性名詞接尾辞' == mrph.bunrui:
                self.logger.debug(f'No volition: {mrph.midasi} is a 形容詞性名詞接尾辞')
                return False

            # 形容詞性述語接尾辞
            if '形容詞性述語接尾辞' == mrph.bunrui:
                # NOTE: 'たい/たい' is not necessary in fact, because it implies the modality of 意志
                if mrph.repname not in {'ない/ない', 'たい/たい'}:
                    self.logger.debug(f'No volition: {mrph.midasi} is a 形容詞性述語接尾辞 which does not imply'
                                      f'volition')
                    return False

            # 動詞性接尾辞
            if '動詞性接尾辞' == mrph.bunrui:
                # 可能接尾辞: 預けておける, 持っていける
                if '可能接尾辞' in mrph.imis:
                    self.logger.debug(f'No volition: {mrph.midasi} is a 可能接尾辞')
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
                    self.logger.debug(f'No volition: {mrph.midasi} is a 動詞性接尾辞 which does not imply volition')
                    return False

        # checks the type
        predicate_type = re.search('<用言:([動形判])>', predicate_tag.fstring).group(1)
        if predicate_type in {'形', '判'}:
            self.logger.debug(f'No volition: the predicate is {predicate_type}')
            return False

        # checks the meaning
        if (predicate_tag.head_prime_repname or predicate_tag.head_repname) in self.exceptional_head_repnames:
            self.logger.debug(f'No volition: this predicate is exceptional')
            return False

        for mrph in reversed(predicate_tag.mrph_list()):
            # 可能動詞: 飲める, 走れる
            if '可能動詞' in mrph.imis:
                self.logger.debug(f'No volition: {mrph.midasi} is a 可能動詞')
                return False

            # 自他動詞:他: 色づく, 削れる
            if '自他動詞:他' in mrph.imis:
                self.logger.debug(f'No volition: {mrph.midasi} is a 自他動詞:他')
                return False

        return True

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

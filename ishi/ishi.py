"""Ishi: A volition classifier for Japanese."""
import pathlib
from logging import getLogger
from typing import Union, Set

from mojimoji import han_to_zen
from pyknp import KNP, BList, Tag

logger = getLogger(__name__)


def has_volition(str_or_blist_or_tag, nominative_str_or_tag=None):
    """Checks if the given input has volition.

    Args:
        str_or_blist_or_tag (Union[str, BList, Tag]): An input string or the language analysis by KNP.
        nominative_str_or_tag (Union[str, Tag], optional): The string or language analysis of the nominative.
            If the nominative comes from exophora resolution, pass the surface string such as '著者' and '読者'.
            Otherwise, pass the language analysis of the nominative with the type of pyknp.Tag.

    Returns:
        bool: True for having volition, False otherwise.

    """
    ishi = Ishi()
    return ishi(str_or_blist_or_tag, nominative_str_or_tag)


class Ishi:
    """Ishi is a volition classifier for Japanese."""

    def __init__(self):
        self._knp = KNP()

        self._valid_nominative_strings = \
            self._load_file('valid_nominative_strings.txt')
        self._valid_nominative_semantic_markers = \
            self._load_file('valid_nominative_semantic_markers.txt')
        self._volition_modalities = \
            self._load_file('volition_modalities.txt')
        self._volition_voices = \
            self._load_file('volition_voices.txt')
        self._non_volition_voices = \
            self._load_file('non_volition_voices.txt')
        self._valid_adjective_predicate_suffix_repnames = \
            self._load_file('valid_adjective_predicate_suffix_repnames.txt')
        self._non_volition_verbal_suffix_semantic_labels = \
            self._load_file('non_volition_verbal_suffix_semantic_labels.txt')
        self._non_volition_verbal_suffix_repnames = \
            self._load_file('non_volition_verbal_suffix_repnames.txt')
        self._non_volition_types = \
            self._load_file('non_volition_types.txt')
        self._non_volition_head_repnames = \
            self._load_file('non_volition_head_repnames.txt')
        self._non_volition_semantic_labels = \
            self._load_file('non_volition_semantic_labels.txt')

    def __call__(self, str_or_blist_or_tag, nominative_str_or_tag=None):
        """Checks if the given input has volition.

        Args:
            str_or_blist_or_tag (Union[str, BList, Tag]): An input string or the language analysis by KNP.
            nominative_str_or_tag (Union[str, Tag], optional): The string or language analysis of the nominative.
                If the nominative comes from exophora resolution, pass the surface string such as '著者' and '読者'.
                Otherwise, pass the language analysis of the nominative with the type of pyknp.Tag.
                If this parameter is None, KNP will analyze the nominative. Care must be taken in that KNP just performs
                case analysis so neither exophora and inter-sentential anaphora will be resolved.

        Returns:
            bool: True for having volition, False otherwise.

        """
        if isinstance(str_or_blist_or_tag, str):
            blist = self._knp.parse(self._preprocess_input_str(str_or_blist_or_tag))
            predicate_tag = self._extract_predicate_tag(blist)
        elif isinstance(str_or_blist_or_tag, BList):
            blist = str_or_blist_or_tag
            predicate_tag = self._extract_predicate_tag(blist)
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
            if nominative_str_or_tag not in self._valid_nominative_strings:
                logger.debug('No volition: the nominative is not a subject')
                return False
        elif isinstance(nominative_str_or_tag, Tag):
            for semantic_marker in self._valid_nominative_semantic_markers:
                if semantic_marker in nominative_str_or_tag.fstring:
                    break
            else:
                logger.debug('No volition: the nominative is not a subject')
                return False
        else:
            logger.warning('Failed to ensure that nominative is a subject')

        # checks the modality
        for modality in self._volition_modalities:
            if modality in predicate_tag.fstring:
                logger.debug(f'Volition: the predicate has the modality of {modality}')
                return True

        # checks the voice
        for voice in self._volition_voices:
            if voice in predicate_tag.fstring:
                logger.debug(f'Volition: the predicate uses the voice of {voice}')
                return True

        for voice in self._non_volition_voices:
            if voice in predicate_tag.fstring:
                logger.debug(f'No volition: the predicate uses the voice of {voice}')
                return False

        # checks the suffix
        for mrph in reversed(predicate_tag.mrph_list()):
            # 形容詞性名詞接尾辞: 風邪気味だ
            if '形容詞性名詞接尾辞' == mrph.bunrui:
                logger.debug(f'No volition: {mrph.midasi} is a 形容詞性名詞接尾辞')
                return False

            # 形容詞性述語接尾辞
            if '形容詞性述語接尾辞' == mrph.bunrui:
                if mrph.repname not in self._valid_adjective_predicate_suffix_repnames:
                    logger.debug(f'No volition: {mrph.midasi} is a 形容詞性述語接尾辞 that does not imply volition')
                    return False

            # 動詞性接尾辞
            if '動詞性接尾辞' == mrph.bunrui:
                for semantic_label in self._non_volition_verbal_suffix_semantic_labels:
                    if semantic_label in mrph.imis:
                        logger.debug(f'No volition: {mrph.midasi} is a {semantic_label}')
                        return False

                if mrph.repname in self._non_volition_verbal_suffix_repnames:
                    logger.debug(f'No volition: {mrph.midasi} is a 動詞性接尾辞 that does not imply volition')
                    return False

        # checks the type
        for type_ in self._non_volition_types:
            if type_ in predicate_tag.fstring:
                logger.debug(f'No volition: the predicate is {type_}')
                return False

        # checks the meaning
        if (predicate_tag.head_prime_repname or predicate_tag.head_repname) in self._non_volition_head_repnames:
            logger.debug(f'No volition: the predicate is exceptional')
            return False

        for mrph in reversed(predicate_tag.mrph_list()):
            for semantic_label in self._non_volition_semantic_labels:
                if semantic_label in mrph.imis:
                    logger.debug(f'No volition: {mrph.midasi} is a {semantic_label}')
                    return False

        return True

    @staticmethod
    def _preprocess_input_str(input_str):
        """Modifies the given input so that the language analyzers can process it.

        Args:
            input_str (str): An input string.

        Returns:
            str: The preprocessed string.

        """
        preprocessed = han_to_zen(input_str)
        return preprocessed

    @staticmethod
    def _extract_predicate_tag(knp_output):
        """Extracts the predicate part from the given KNP output.

        Args:
            knp_output (BList): A KNP output.

        Returns:
            Tag

        """
        for tag in reversed(knp_output.tag_list()):
            if '用言' in tag.features:
                return tag
        else:
            return knp_output.tag_list()[-1]

    @staticmethod
    def _load_file(filename):
        """Loads a rule written as a text file.

        Args:
            filename (str): The name of a rule file.

        Returns:
            Set[str]

        """
        path = pathlib.Path(__file__).parent / 'rules' / filename
        with path.open(encoding='utf-8') as f:
            return set(line.strip() for line in f)

import json
import os
from typing import Dict, List, Optional, Set

from .deconjugation_form import DeconjugationForm
from .deconjugation_rule import DeconjugationRule
from .deconjugation_virtual_rule import DeconjugationVirtualRule


class Deconjugator:
    """
    Handles the de-conjugation of Japanese words by applying a set of rules.
    """

    _deconjugation_cache: Dict[str, Set[DeconjugationForm]] = {}
    USE_CACHE: bool = False

    def __init__(self):
        """
        Initializes the Deconjugator by loading and processing de-conjugation rules
        from a JSON file.
        """
        self.rules: List[DeconjugationRule] = []
        self._virtual_rules_cache: Dict[int, List[DeconjugationVirtualRule]] = {}

        resources_path = os.path.join(os.path.dirname(__file__), "resources", "deconjugator.json")        
        with open(resources_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)

        for i, rule_dict in enumerate(rules_data):
            rule = DeconjugationRule.from_dict(rule_dict)
            self.rules.append(rule)
            self._cache_virtual_rules(rule, i)

    def _cache_virtual_rules(self, rule: DeconjugationRule, rule_index: int):
        """
        Pre-calculates and caches virtual rules for rules with multiple endings.
        This avoids repeated object creation during the de-conjugation process.
        """
        if len(rule.dec_end) <= 1:
            return

        virtual_rules = []
        for i in range(len(rule.dec_end)):
            dec_end = rule.dec_end[i] if i < len(rule.dec_end) else rule.dec_end[0]
            con_end = rule.con_end[i] if i < len(rule.con_end) else rule.con_end[0]
            
            dec_tag = None
            if rule.dec_tag:
                dec_tag = rule.dec_tag[i] if i < len(rule.dec_tag) else rule.dec_tag[0]

            con_tag = None
            if rule.con_tag:
                con_tag = rule.con_tag[i] if i < len(rule.con_tag) else rule.con_tag[0]

            virtual_rules.append(DeconjugationVirtualRule(
                dec_end=dec_end,
                con_end=con_end,
                dec_tag=dec_tag,
                con_tag=con_tag,
                detail=rule.detail
            ))
        self._virtual_rules_cache[rule_index] = virtual_rules

    def deconjugate(self, text: str) -> Set[DeconjugationForm]:
        """
        Performs de-conjugation on the input text.

        It iteratively applies rules to find all possible dictionary forms.
        """
        if self.USE_CACHE and text in self._deconjugation_cache:
            return set(self._deconjugation_cache[text])

        processed: Set[DeconjugationForm] = set()
        if not text:
            return processed

        novel: Set[DeconjugationForm] = set()
        start_form = self._create_initial_form(text)
        novel.add(start_form)

        while novel:
            new_novel: Set[DeconjugationForm] = set()
            
            for form in novel:
                if self._should_skip_form(form):
                    continue

                for i, rule in enumerate(self.rules):
                    new_forms = self._apply_rule(form, rule, i)

                    if not new_forms:
                        continue

                    for f in new_forms:
                        if f not in processed and f not in novel and f not in new_novel:
                            new_novel.add(f)
            
            processed.update(novel)
            novel = new_novel

        if self.USE_CACHE and len(text) <= 20 and len(processed) < 55 and len(self._deconjugation_cache) < 250000:
            self._deconjugation_cache[text] = set(processed)

        return processed

    def _create_initial_form(self, text: str) -> DeconjugationForm:
        """Creates the starting DeconjugationForm for a given text."""
        return DeconjugationForm(text=text, original_text=text, tags=[], seen_text=set(), process=[])

    def _should_skip_form(self, form: DeconjugationForm) -> bool:
        """Determines if a form should be skipped to avoid excessive processing."""
        return (not form.text or
                len(form.text) > len(form.original_text) + 10 or
                len(form.tags) > len(form.original_text) + 6)

    def _apply_rule(self, form: DeconjugationForm, rule: DeconjugationRule, rule_index: int) -> Optional[Set[DeconjugationForm]]:
        """
        Dispatcher that applies the correct de-conjugation logic based on the rule type.
        """
        rule_type = rule.type
        if rule_type == "stdrule":
            return self._std_rule_deconjugate(form, rule, rule_index)
        if rule_type == "rewriterule":
            return self._rewrite_rule_deconjugate(form, rule, rule_index)
        if rule_type == "onlyfinalrule":
            return self._only_final_rule_deconjugate(form, rule, rule_index)
        if rule_type == "neverfinalrule":
            return self._never_final_rule_deconjugate(form, rule, rule_index)
        if rule_type == "contextrule":
            return self._context_rule_deconjugate(form, rule, rule_index)
        if rule_type == "substitution":
            return self._substitution_deconjugate(form, rule)
        return None

    def _std_rule_deconjugate(self, form: DeconjugationForm, rule: DeconjugationRule, rule_index: int) -> Optional[Set[DeconjugationForm]]:
        """Applies a standard de-conjugation rule."""
        if not rule.detail and not form.tags:
            return None

        if len(rule.dec_end) == 1:
            virtual_rule = DeconjugationVirtualRule(
                dec_end=rule.dec_end[0],
                con_end=rule.con_end[0],
                dec_tag=rule.dec_tag[0] if rule.dec_tag else None,
                con_tag=rule.con_tag[0] if rule.con_tag else None,
                detail=rule.detail
            )
            hit = self._std_rule_deconjugate_inner(form, virtual_rule)
            return {hit} if hit else None

        cached_virtual_rules = self._virtual_rules_cache.get(rule_index)
        if not cached_virtual_rules:
            return None

        collection = set()
        for virtual_rule in cached_virtual_rules:
            hit = self._std_rule_deconjugate_inner(form, virtual_rule)
            if hit:
                collection.add(hit)
        
        return collection if collection else None

    def _std_rule_deconjugate_inner(self, form: DeconjugationForm, rule: DeconjugationVirtualRule) -> Optional[DeconjugationForm]:
        """The core logic for applying a standard de-conjugation rule."""
        if not form.text.endswith(rule.con_end):
            return None

        if form.tags and form.tags[-1] != rule.con_tag:
            return None

        prefix_len = len(form.text) - len(rule.con_end)
        new_text = form.text[:prefix_len] + rule.dec_end

        if new_text == form.original_text:
            return None

        return self._create_new_form(form, new_text, rule.con_tag, rule.dec_tag, rule.detail)

    def _create_new_form(self, form: DeconjugationForm, new_text: str, con_tag: Optional[str], dec_tag: Optional[str], detail: str) -> DeconjugationForm:
        """Creates a new DeconjugationForm based on an existing one after applying a rule."""
        new_tags = list(form.tags)
        new_seen_text = set(form.seen_text)
        new_process = list(form.process)

        new_process.append(detail)

        if not new_tags and con_tag is not None:
            new_tags.append(con_tag)

        if dec_tag is not None:
            new_tags.append(dec_tag)

        if not new_seen_text:
            new_seen_text.add(form.text)
        new_seen_text.add(new_text)

        return DeconjugationForm(new_text, form.original_text, new_tags, new_seen_text, new_process)

    def _substitution_deconjugate(self, form: DeconjugationForm, rule: DeconjugationRule) -> Optional[Set[DeconjugationForm]]:
        """Applies a substitution rule."""
        if form.process or not form.text:
            return None

        if len(rule.dec_end) == 1:
            hit = self._substitution_inner(form, rule.con_end[0], rule.dec_end[0], rule.detail)
            return {hit} if hit else None

        collection = set()
        for i in range(len(rule.dec_end)):
            dec_end = rule.dec_end[i] if i < len(rule.dec_end) else rule.dec_end[0]
            con_end = rule.con_end[i] if i < len(rule.con_end) else rule.con_end[0]
            
            ret = self._substitution_inner(form, con_end, dec_end, rule.detail)
            if ret:
                collection.add(ret)
        
        return collection if collection else None

    def _substitution_inner(self, form: DeconjugationForm, con_end: str, dec_end: str, detail: str) -> Optional[DeconjugationForm]:
        """The core logic for applying a substitution."""
        if con_end not in form.text:
            return None
        
        new_text = form.text.replace(con_end, dec_end)
        return self._create_substitution_form(form, new_text, detail)

    def _create_substitution_form(self, form: DeconjugationForm, new_text: str, detail: str) -> DeconjugationForm:
        """Creates a new form after a substitution."""
        new_seen_text = set(form.seen_text)
        new_process = list(form.process)
        new_tags = list(form.tags)

        new_process.append(detail)

        if not new_seen_text:
            new_seen_text.add(form.text)
        new_seen_text.add(new_text)

        return DeconjugationForm(new_text, form.original_text, new_tags, new_seen_text, new_process)

    def _rewrite_rule_deconjugate(self, form: DeconjugationForm, rule: DeconjugationRule, rule_index: int) -> Optional[Set[DeconjugationForm]]:
        """Applies a rule only if the form's text exactly matches the conjugated ending."""
        return self._std_rule_deconjugate(form, rule, rule_index) if form.text == rule.con_end[0] else None

    def _only_final_rule_deconjugate(self, form: DeconjugationForm, rule: DeconjugationRule, rule_index: int) -> Optional[Set[DeconjugationForm]]:
        """Applies a rule only if it's the first rule in the chain (no tags yet)."""
        return self._std_rule_deconjugate(form, rule, rule_index) if not form.tags else None

    def _never_final_rule_deconjugate(self, form: DeconjugationForm, rule: DeconjugationRule, rule_index: int) -> Optional[Set[DeconjugationForm]]:
        """Applies a rule only if it's not the first rule in the chain (tags exist)."""
        return self._std_rule_deconjugate(form, rule, rule_index) if form.tags else None

    def _context_rule_deconjugate(self, form: DeconjugationForm, rule: DeconjugationRule, rule_index: int) -> Optional[Set[DeconjugationForm]]:
        if rule.context_rule == "v1inftrap" and not self._v1_inf_trap_check(form):
            return None
        if rule.context_rule == "saspecial" and not self._sa_special_check(form, rule):
            return None
        
        return self._std_rule_deconjugate(form, rule, rule_index)

    def _v1_inf_trap_check(self, form: DeconjugationForm) -> bool:
        return form.tags != ["stem-ren"]

    def _sa_special_check(self, form: DeconjugationForm, rule: DeconjugationRule) -> bool:
        if not form.text:
            return False

        con_end = rule.con_end[0]
        if not form.text.endswith(con_end):
            return False

        prefix_len = len(form.text) - len(con_end)
        return prefix_len <= 0 or form.text[prefix_len - 1] != "さ"
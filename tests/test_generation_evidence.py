import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('fresh_generations',ROOT/'scripts/run_fresh_generations.py')
RUNNER=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class GenerationIsolationTests(unittest.TestCase):
    def test_baseline_receives_no_skills_or_other_condition_outputs(self):
        source={'sentinel':'only the intended English input'}
        with tempfile.TemporaryDirectory() as temporary:
            workspace=Path(temporary)
            (workspace/'baseline').mkdir()
            (workspace/'baseline/output.json').write_text(json.dumps({'sentinel':'must not leak'}),encoding='utf8')
            self.assertEqual(RUNNER.build_inputs('baseline',workspace,source),{'source_pack':source})

    def test_duplicate_or_missing_fragment_cannot_be_accepted_as_complete(self):
        inputs={'source_pack':{'fragments':[{'id':'one'},{'id':'two'}]}}
        duplicated={'translations':[{'id':'one','text':'A complete sufficiently long passage.'}]*2}
        with self.assertRaises(AssertionError):
            RUNNER.validate_output('skilled',duplicated,inputs)

    def test_reference_translation_field_is_rejected_before_generation(self):
        contaminated={'source_language':'English','target_language':'Russian','scope':'sample','works':[], 'fragments':[], 'human_text':'reference translation'}
        with self.assertRaises(AssertionError):
            RUNNER.validate_source_pack(contaminated)

    def test_ignored_isolation_setting_cannot_be_accepted_as_evidence(self):
        events=[{'type':'thread.started','thread_id':'new-session'}, {'type':'item.completed','item':{'type':'error','message':'session-flags: features.shell_tool is ignored.'}}]
        with self.assertRaises(AssertionError):
            RUNNER.inspect_events(events)

    def test_tool_call_cannot_be_accepted_as_isolated_generation(self):
        events=[{'type':'thread.started','thread_id':'new-session'}, {'type':'item.completed','item':{'type':'command_execution'}}]
        with self.assertRaises(AssertionError):
            RUNNER.inspect_events(events)


if __name__=='__main__':
    unittest.main()

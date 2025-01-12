import logging
from attackmate.schemas.playbook import Commands
from attackmate.schemas.debug import DebugCommand
from attackmate.schemas.loop import LoopCommand
from attackmate.schemas.sleep import SleepCommand
from attackmate.executors.common.debugexecutor import DebugExecutor
from attackmate.executors.common.loopexecutor import LoopExecutor
from attackmate.executors.common.sleepexecutor import SleepExecutor
from attackmate.variablestore import VariableStore
from attackmate.processmanager import ProcessManager


class TestLoopExecutor:
    def setup_method(self, method):
        self.varstore = VariableStore()
        self.process_manager = ProcessManager()
        self.sleep_executor = SleepExecutor(self.process_manager, varstore=self.varstore)
        self.debug_executor = DebugExecutor(self.process_manager, self.varstore)
        self.loop_executor = LoopExecutor(self.process_manager, varstore=self.varstore, runfunc=self.run_func)

    def run_func(self, commands: Commands):
        for command in commands:
            if command.type == 'debug':
                self.debug_executor.run(command)
            elif command.type == 'sleep':
                self.sleep_executor.run(command)

    def test_items(self, caplog):
        caplog.set_level(logging.INFO)
        self.varstore.clear()
        self.varstore.set_variable('one', ['first', 'second'])
        lc = LoopCommand(
            type='loop', cmd='items($one)', commands=[DebugCommand(cmd='$LOOP_ITEM', type='debug')]
        )
        self.loop_executor.run(lc)
        assert 'Debug: \'first\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'second\'' in [rec.message for rec in caplog.records]

    def test_range(self, caplog):
        caplog.set_level(logging.INFO)
        self.varstore.clear()
        self.varstore.set_variable('one', ['first', 'second'])
        lc = LoopCommand(
            type='loop', cmd='range(1,3)', commands=[DebugCommand(cmd='$LOOP_INDEX', type='debug')]
        )
        self.loop_executor.run(lc)
        assert 'Debug: \'1\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'2\'' in [rec.message for rec in caplog.records]

    def test_until(self, caplog):
        caplog.set_level(logging.INFO)
        self.varstore.clear()
        lc = LoopCommand(
            type='loop',
            cmd='until($LOOP_INDEX == 2)',
            commands=[DebugCommand(cmd='$LOOP_INDEX', type='debug')],
        )
        self.loop_executor.run(lc)
        # Verify that the loop ran exactly 2 times
        assert 'Debug: \'0\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'1\'' in [rec.message for rec in caplog.records]
        assert 'Debug: \'2\'' not in [rec.message for rec in caplog.records]

    def test_range_with_sleep(self, caplog):
        """
        Test that $LOOP_INDEX is substituted correctly for a range-based loop.
        The sleep command ensures substitution works in fields like "seconds," beyond just "cmd".
        """
        caplog.set_level(logging.INFO)
        self.varstore.clear()
        lc = LoopCommand(
            type='loop',
            cmd='range(0,3)',
            commands=[
                SleepCommand(type='sleep', cmd='sleep', seconds='$LOOP_INDEX'),
            ],
        )
        self.loop_executor.run(lc)
        expected_logs = [
            'Sleeping 0 seconds',
            'Sleeping 1 seconds',
            'Sleeping 2 seconds',
        ]
        # Verify the expected log messages
        for log in expected_logs:
            assert log in [rec.message for rec in caplog.records]

    def test_items_with_sleep(self, caplog):
        """
        Test that $LOOP_ITEM is substituted correctly for a list-based loop.
        The sleep command ensures substitution works in fields like "seconds," beyond just "cmd".
        """
        caplog.set_level(logging.INFO)
        self.varstore.clear()
        self.varstore.set_variable('LISTA', [1, 2])
        lc = LoopCommand(
            type='loop',
            cmd='items(LISTA)',
            commands=[
                SleepCommand(type='sleep', cmd='sleep', seconds='$LOOP_ITEM'),
            ],
        )
        self.loop_executor.run(lc)
        expected_logs = [
            'Sleeping 1 seconds',
            'Sleeping 2 seconds',
        ]
        # Verify the expected log messages
        for log in expected_logs:
            assert log in [rec.message for rec in caplog.records]

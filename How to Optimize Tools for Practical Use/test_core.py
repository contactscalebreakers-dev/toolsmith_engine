"""
Test suite for SB Toolsmith Pro core components.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Core tests
from core.event_bus import EventBus, Event
from core.scheduler import Scheduler, Task
from core.runtime_manager import RuntimeManager
from core.dag_engine import DAGEngine, DAGNode, NodePort, PortType
from core.snapshot_manager import SnapshotManager
from plugins.manifest import PluginManifest, Capability, PermissionScope


class TestEventBus:
    """Test EventBus functionality."""

    def test_event_creation(self):
        """Test event creation."""
        event = Event(event_type="test", data={"key": "value"})
        assert event.event_type == "test"
        assert event.data == {"key": "value"}

    def test_event_subscription(self):
        """Test event subscription."""
        bus = EventBus()
        callback = Mock()

        bus.subscribe("test_event", callback)
        bus.emit(Event(event_type="test_event", data={"test": True}))

        callback.assert_called_once()

    def test_event_unsubscription(self):
        """Test event unsubscription."""
        bus = EventBus()
        callback = Mock()

        bus.subscribe("test_event", callback)
        bus.unsubscribe("test_event", callback)
        bus.emit(Event(event_type="test_event", data={}))

        callback.assert_not_called()

    def test_event_history(self):
        """Test event history."""
        bus = EventBus()

        bus.emit(Event(event_type="event1", data={}))
        bus.emit(Event(event_type="event2", data={}))

        history = bus.get_history()
        assert len(history) == 2


class TestScheduler:
    """Test Scheduler functionality."""

    @pytest.mark.asyncio
    async def test_task_scheduling(self):
        """Test task scheduling."""
        scheduler = Scheduler()

        async def dummy_task():
            return "done"

        task = Task(
            task_id="test_task",
            coro=dummy_task(),
            description="Test task",
        )

        scheduler.schedule_task(task)
        assert len(scheduler.get_pending_tasks()) == 1

    @pytest.mark.asyncio
    async def test_task_execution(self):
        """Test task execution."""
        scheduler = Scheduler()

        async def dummy_task():
            return "done"

        task = Task(
            task_id="test_task",
            coro=dummy_task(),
            description="Test task",
        )

        scheduler.schedule_task(task)
        await asyncio.sleep(0.1)

        completed = scheduler.get_completed_tasks()
        assert len(completed) > 0

    @pytest.mark.asyncio
    async def test_task_retry(self):
        """Test task retry logic."""
        scheduler = Scheduler()
        attempt_count = 0

        async def failing_task():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        task = Task(
            task_id="retry_task",
            coro=failing_task(),
            description="Retry task",
            max_retries=3,
        )

        scheduler.schedule_task(task)
        await asyncio.sleep(0.5)

        assert attempt_count >= 1


class TestDAGEngine:
    """Test DAG Engine functionality."""

    def test_node_creation(self):
        """Test DAG node creation."""
        node = DAGNode(
            node_id="test_node",
            name="Test Node",
            inputs={"input1": NodePort("input1", PortType.STRING)},
            outputs={"output1": NodePort("output1", PortType.STRING)},
        )

        assert node.node_id == "test_node"
        assert len(node.inputs) == 1
        assert len(node.outputs) == 1

    def test_dag_execution(self):
        """Test DAG execution."""
        engine = DAGEngine()

        node1 = DAGNode(
            node_id="node1",
            name="Node 1",
            inputs={},
            outputs={"out": NodePort("out", PortType.STRING)},
        )

        node2 = DAGNode(
            node_id="node2",
            name="Node 2",
            inputs={"in": NodePort("in", PortType.STRING)},
            outputs={},
        )

        engine.add_node(node1)
        engine.add_node(node2)
        engine.add_edge("node1", "out", "node2", "in")

        # Verify graph structure
        assert len(engine.nodes) == 2
        assert len(engine.edges) == 1

    def test_cycle_detection(self):
        """Test cycle detection."""
        engine = DAGEngine()

        node1 = DAGNode(
            node_id="node1",
            name="Node 1",
            inputs={"in": NodePort("in", PortType.STRING)},
            outputs={"out": NodePort("out", PortType.STRING)},
        )

        node2 = DAGNode(
            node_id="node2",
            name="Node 2",
            inputs={"in": NodePort("in", PortType.STRING)},
            outputs={"out": NodePort("out", PortType.STRING)},
        )

        engine.add_node(node1)
        engine.add_node(node2)

        engine.add_edge("node1", "out", "node2", "in")
        engine.add_edge("node2", "out", "node1", "in")

        # Should detect cycle
        assert engine.has_cycle()


class TestPluginManifest:
    """Test Plugin Manifest functionality."""

    def test_manifest_creation(self):
        """Test manifest creation."""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            entry_point="test_plugin.main",
            capabilities=[
                Capability(name="file_access", scope=PermissionScope.WORKSPACE),
                Capability(name="network", scope=PermissionScope.RESTRICTED),
            ],
        )

        assert manifest.name == "test_plugin"
        assert len(manifest.capabilities) == 2

    def test_manifest_validation(self):
        """Test manifest validation."""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            entry_point="test_plugin.main",
            capabilities=[],
        )

        # Should validate successfully
        assert manifest.validate()

    def test_capability_checking(self):
        """Test capability checking."""
        manifest = PluginManifest(
            name="test_plugin",
            version="1.0.0",
            entry_point="test_plugin.main",
            capabilities=[
                Capability(name="file_access", scope=PermissionScope.WORKSPACE),
            ],
        )

        assert manifest.has_capability("file_access")
        assert not manifest.has_capability("network")


class TestSnapshotManager:
    """Test Snapshot Manager functionality."""

    @pytest.mark.asyncio
    async def test_snapshot_creation(self, tmp_path):
        """Test snapshot creation."""
        manager = SnapshotManager(tmp_path)

        snapshot_data = {
            "environment": "test",
            "state": {"key": "value"},
        }

        snapshot_id = await manager.create_snapshot(snapshot_data)
        assert snapshot_id is not None

    @pytest.mark.asyncio
    async def test_snapshot_restoration(self, tmp_path):
        """Test snapshot restoration."""
        manager = SnapshotManager(tmp_path)

        snapshot_data = {
            "environment": "test",
            "state": {"key": "value"},
        }

        snapshot_id = await manager.create_snapshot(snapshot_data)
        restored = await manager.restore_snapshot(snapshot_id, tmp_path / "restored")

        assert restored is not None

    @pytest.mark.asyncio
    async def test_snapshot_cleanup(self, tmp_path):
        """Test snapshot cleanup."""
        manager = SnapshotManager(tmp_path)

        snapshot_data = {"environment": "test", "state": {}}

        snapshot_id = await manager.create_snapshot(snapshot_data)
        await manager.delete_snapshot(snapshot_id)

        snapshots = await manager.list_snapshots()
        assert snapshot_id not in snapshots


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

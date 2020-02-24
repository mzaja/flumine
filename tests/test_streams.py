import unittest
from unittest import mock

from flumine.streams import streams, datastream
from flumine.streams.basestream import BaseStream
from flumine.exceptions import ListenerError


class StreamsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.streams = streams.Streams(self.mock_flumine)

    def test_init(self):
        self.assertEqual(self.streams.flumine, self.mock_flumine)
        self.assertEqual(self.streams._streams, [])
        self.assertEqual(self.streams._stream_id, 0)

    @mock.patch("flumine.streams.streams.Streams.add_market_stream")
    def test_call(self, mock__add_stream):
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.raw_data = False
        self.streams(mock_strategy)

        mock__add_stream.assert_called_with(mock_strategy, streams.MarketStream)
        self.assertEqual(len(mock_strategy.streams), 1)

    @mock.patch("flumine.streams.streams.Streams.add_market_stream")
    def test_call_data_stream(self, mock__add_stream):
        mock_strategy = mock.Mock()
        mock_strategy.streams = []
        mock_strategy.data_stream = True
        self.streams(mock_strategy)

        mock__add_stream.assert_called_with(mock_strategy, streams.DataStream)
        self.assertEqual(len(mock_strategy.streams), 1)

    @mock.patch("flumine.streams.streams.MarketStream")
    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_market_stream_new(self, mock_increment, mock_market_streaming):
        mock_strategy = mock.Mock()

        self.streams.add_market_stream(mock_strategy, streams.MarketStream)
        self.assertEqual(len(self.streams), 1)
        mock_increment.assert_called_with()
        mock_market_streaming.assert_called_with(
            self.mock_flumine,
            mock_increment(),
            mock_strategy.market_filter,
            mock_strategy.market_data_filter,
            mock_strategy.streaming_timeout,
            mock_strategy.conflate_ms,
        )

    @mock.patch("flumine.streams.streams.Streams._increment_stream_id")
    def test_add_market_stream_old(self, mock_increment):
        mock_strategy = mock.Mock()
        mock_strategy.market_filter = 1
        mock_strategy.market_data_filter = 2
        mock_strategy.streaming_timeout = 3
        mock_strategy.conflate_ms = 4

        stream = mock.Mock(spec=streams.MarketStream)
        stream.market_filter = 1
        stream.market_data_filter = 2
        stream.streaming_timeout = 3
        stream.conflate_ms = 4
        stream.stream_id = 1001
        self.streams._streams = [stream]

        new_stream = self.streams.add_market_stream(mock_strategy, streams.MarketStream)
        self.assertEqual(len(self.streams), 1)
        self.assertEqual(stream, new_stream)
        mock_increment.assert_not_called()

    def test_start(self):
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.start()
        mock_stream.start.assert_called()

    def test_stop(self):
        mock_stream = mock.Mock()
        self.streams._streams = [mock_stream]
        self.streams.stop()
        mock_stream.stop.assert_called()

    def test__increment_stream_id(self):
        self.assertEqual(self.streams._increment_stream_id(), 1000)

    def test_iter(self):
        for i in self.streams:
            assert i

    def test_len(self):
        self.assertEqual(len(self.streams), 0)


class TestBaseStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = BaseStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.stream.run()

    def test_handle_output(self):
        with self.assertRaises(NotImplementedError):
            self.stream.handle_output()

    def test_stop(self):
        mock_stream = mock.Mock()
        self.stream._stream = mock_stream
        self.stream.stop()
        mock_stream.stop.assert_called()

    def test_trading(self):
        self.assertEqual(self.stream.trading, self.mock_flumine.trading)


class TestMarketStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.MarketStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)

    # def test_run(self):
    #     pass
    #
    # def test_handle_output(self):
    #     pass


class TestDataStream(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_flumine = mock.Mock()
        self.stream = streams.DataStream(
            self.mock_flumine, 123, {"test": "me"}, {"please": "now"}, 0.01, 100
        )

    def test_init(self):
        self.assertEqual(self.stream.flumine, self.mock_flumine)
        self.assertEqual(self.stream.stream_id, 123)
        self.assertEqual(self.stream.market_filter, {"test": "me"})
        self.assertEqual(self.stream.market_data_filter, {"please": "now"})
        self.assertEqual(self.stream.streaming_timeout, 0.01)
        self.assertEqual(self.stream.conflate_ms, 100)
        self.assertIsNone(self.stream._stream)
        self.assertEqual(self.stream.LISTENER, datastream.FlumineListener)

    # def test_run(self):
    #     pass
    #
    # def test_handle_output(self):
    #     pass

    @mock.patch("flumine.streams.datastream.FlumineRaceStream")
    @mock.patch("flumine.streams.datastream.FlumineMarketStream")
    def test_flumine_listener(self, mock_market_stream, mock_race_stream):
        listener = datastream.FlumineListener()
        self.assertEqual(
            listener._add_stream(123, "marketSubscription"), mock_market_stream()
        )

        with self.assertRaises(ListenerError):
            listener._add_stream(123, "orderSubscription")

        listener = datastream.FlumineListener()
        self.assertEqual(
            listener._add_stream(123, "raceSubscription"), mock_race_stream()
        )

    def test_flumine_stream(self):
        mock_listener = mock.Mock()
        stream = datastream.FlumineStream(mock_listener)
        self.assertEqual(str(stream), "FlumineStream")
        self.assertEqual(repr(stream), "<FlumineStream [0]>")

    @mock.patch("flumine.streams.datastream.FlumineMarketStream.on_process")
    def test_flumine_market_stream(self, mock_on_process):
        mock_listener = mock.Mock()
        stream = datastream.FlumineMarketStream(mock_listener)
        market_books = [{"id": "1.123"}, {"id": "1.456"}, {"id": "1.123"}]
        stream._process(market_books, 123)

        self.assertEqual(len(stream._caches), 2)
        self.assertEqual(stream._updates_processed, 3)
        mock_on_process.assert_called_with(
            (mock_listener.stream_unique_id, 123, market_books)
        )

    @mock.patch("flumine.streams.datastream.FlumineMarketStream.on_process")
    def test_flumine_market_stream_market_closed(self, mock_on_process):
        mock_listener = mock.Mock()
        stream = datastream.FlumineMarketStream(mock_listener)
        stream._caches = {"1.123": object}
        market_books = [{"id": "1.123", "marketDefinition": {"status": "CLOSED"}}]
        stream._process(market_books, 123)

        self.assertEqual(stream._lookup, "mc")
        self.assertEqual(len(stream._caches), 0)
        self.assertEqual(stream._updates_processed, 1)
        mock_on_process.assert_called_with(
            (mock_listener.stream_unique_id, 123, market_books)
        )

    @mock.patch("flumine.streams.datastream.FlumineRaceStream.on_process")
    def test_flumine_race_stream(self, mock_on_process):
        mock_listener = mock.Mock()
        stream = datastream.FlumineRaceStream(mock_listener)
        race_updates = [{"mid": "1.123"}, {"mid": "1.456"}, {"mid": "1.123"}]
        stream._process(race_updates, 123)

        self.assertEqual(stream._lookup, "rc")
        self.assertEqual(len(stream._caches), 2)
        self.assertEqual(stream._updates_processed, 3)
        mock_on_process.assert_called_with(
            (mock_listener.stream_unique_id, 123, race_updates)
        )

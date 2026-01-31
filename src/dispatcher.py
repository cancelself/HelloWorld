"""HelloWorld Dispatcher - Routes parsed AST nodes to receiver handlers."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lexer import Lexer
from parser import (
    Parser, Statement, VocabularyDefinition, VocabularyQuery,
    SymbolLookup, Message, ValueType,
)


@dataclass
class Receiver:
    name: str
    vocabulary: List[str] = field(default_factory=list)


@dataclass
class DispatchResult:
    kind: str  # "vocabulary", "scoped_lookup", "message", "definition", "error"
    receiver: str
    data: dict = field(default_factory=dict)


class ReceiverRegistry:
    def __init__(self):
        self._receivers: Dict[str, Receiver] = {}

    def register(self, name: str, vocabulary: Optional[List[str]] = None) -> Receiver:
        if name not in self._receivers:
            self._receivers[name] = Receiver(name, vocabulary or [])
        elif vocabulary:
            self._receivers[name].vocabulary = vocabulary
        return self._receivers[name]

    def get(self, name: str) -> Optional[Receiver]:
        return self._receivers.get(name)

    def has(self, name: str) -> bool:
        return name in self._receivers

    def vocabulary(self, name: str) -> List[str]:
        receiver = self.get(name)
        if receiver is None:
            return []
        return list(receiver.vocabulary)

    def has_symbol(self, receiver_name: str, symbol: str) -> bool:
        receiver = self.get(receiver_name)
        if receiver is None:
            return False
        return symbol in receiver.vocabulary

    def add_symbol(self, receiver_name: str, symbol: str):
        receiver = self.get(receiver_name)
        if receiver and symbol not in receiver.vocabulary:
            receiver.vocabulary.append(symbol)

    def receivers(self) -> List[str]:
        return list(self._receivers.keys())


def _bootstrap_registry() -> ReceiverRegistry:
    registry = ReceiverRegistry()
    registry.register("@awakener", [
        "#stillness", "#entropy", "#intention", "#sleep", "#insight",
    ])
    registry.register("@guardian", [
        "#fire", "#vision", "#challenge", "#gift", "#threshold",
    ])
    registry.register("@claude", [
        "#parse", "#dispatch", "#state", "#collision", "#entropy", "#meta",
    ])
    return registry


class Dispatcher:
    def __init__(self, registry: Optional[ReceiverRegistry] = None):
        self.registry = registry or _bootstrap_registry()

    def dispatch(self, source: str) -> List[DispatchResult]:
        statements = Parser.from_source(source).parse()
        return self.dispatch_statements(statements)

    def dispatch_statements(self, statements: List[Statement]) -> List[DispatchResult]:
        results = []
        for stmt in statements:
            result = self._dispatch_statement(stmt)
            if result:
                results.append(result)
        return results

    def _dispatch_statement(self, stmt: Statement) -> Optional[DispatchResult]:
        if isinstance(stmt, VocabularyDefinition):
            return self._handle_definition(stmt)
        if isinstance(stmt, VocabularyQuery):
            return self._handle_vocabulary_query(stmt)
        if isinstance(stmt, SymbolLookup):
            return self._handle_scoped_lookup(stmt)
        if isinstance(stmt, Message):
            return self._handle_message(stmt)
        return None

    def _handle_definition(self, stmt: VocabularyDefinition) -> DispatchResult:
        self.registry.register(stmt.receiver, list(stmt.symbols))
        return DispatchResult(
            kind="definition",
            receiver=stmt.receiver,
            data={"vocabulary": list(stmt.symbols)},
        )

    def _handle_vocabulary_query(self, stmt: VocabularyQuery) -> DispatchResult:
        if not self.registry.has(stmt.receiver):
            return DispatchResult(
                kind="error",
                receiver=stmt.receiver,
                data={"error": f"Unknown receiver: {stmt.receiver}"},
            )
        return DispatchResult(
            kind="vocabulary",
            receiver=stmt.receiver,
            data={"vocabulary": self.registry.vocabulary(stmt.receiver)},
        )

    def _handle_scoped_lookup(self, stmt: SymbolLookup) -> DispatchResult:
        if not self.registry.has(stmt.receiver):
            return DispatchResult(
                kind="error",
                receiver=stmt.receiver,
                data={"error": f"Unknown receiver: {stmt.receiver}"},
            )
        native = self.registry.has_symbol(stmt.receiver, stmt.symbol)
        return DispatchResult(
            kind="scoped_lookup",
            receiver=stmt.receiver,
            data={
                "symbol": stmt.symbol,
                "native": native,
                "vocabulary": self.registry.vocabulary(stmt.receiver),
            },
        )

    def _handle_message(self, stmt: Message) -> DispatchResult:
        if not self.registry.has(stmt.receiver):
            return DispatchResult(
                kind="error",
                receiver=stmt.receiver,
                data={"error": f"Unknown receiver: {stmt.receiver}"},
            )
        arguments = {}
        for kw in stmt.keywords:
            arguments[kw.name] = kw.value.value

        collisions = []
        for kw in stmt.keywords:
            if kw.value.kind == ValueType.SYMBOL:
                if not self.registry.has_symbol(stmt.receiver, kw.value.value):
                    collisions.append(kw.value.value)

        return DispatchResult(
            kind="message",
            receiver=stmt.receiver,
            data={
                "arguments": arguments,
                "annotation": stmt.annotation,
                "collisions": collisions,
                "vocabulary": self.registry.vocabulary(stmt.receiver),
            },
        )

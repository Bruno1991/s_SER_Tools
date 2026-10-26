"""Extrator avançado de strings, URLs, IPs e padrões de binários e arquivos de código."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Union


@dataclass
class ExtractedPatternMatch:
    kind: str
    value: str
    offset: Optional[int] = None


@dataclass
class StringsResult:
    total_strings: int
    ascii_strings: List[str] = field(default_factory=list)
    unicode_strings: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    ip_addresses: List[str] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)


class StringsExtractor:
    """Extrai strings legíveis (ASCII/UTF-16LE) e padrões de segurança de qualquer arquivo binário."""

    URL_REGEX = re.compile(r"https?://(?:[a-zA-Z0-9$-_@.&+!*\\(\\),]|(?:%[0-9a-fA-F]{2}))+", re.IGNORECASE)
    IP_REGEX = re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    PATH_REGEX = re.compile(r"(?:[a-zA-Z]:\\(?:[^<>:\"/\\|?*\n\r]+\\)*[^<>:\"/\\|?*\n\r]+)|(?:/(?:[a-zA-Z0-9._-]+/)+[a-zA-Z0-9._-]+)")

    @classmethod
    def extract_from_bytes(cls, data: bytes, min_len: int = 4, max_strings: int = 5000) -> StringsResult:
        """Varre bytes em memória e extrai strings ASCII e Unicode."""
        ascii_matches: List[str] = []
        unicode_matches: List[str] = []

        # ASCII regex: caracteres imprimíveis entre 0x20 e 0x7E
        ascii_pattern = re.compile(rb"[\x20-\x7e]{" + str(min_len).encode() + rb",}")
        for match in ascii_pattern.finditer(data):
            if len(ascii_matches) >= max_strings:
                break
            try:
                ascii_matches.append(match.group().decode("latin-1"))
            except Exception:
                pass

        # UTF-16LE regex: caractere ASCII seguido de 0x00
        utf16_pattern = re.compile(rb"(?:[\x20-\x7e]\x00){" + str(min_len).encode() + rb",}")
        for match in utf16_pattern.finditer(data):
            if len(unicode_matches) >= max_strings:
                break
            try:
                unicode_matches.append(match.group().decode("utf-16le"))
            except Exception:
                pass

        all_combined = ascii_matches + unicode_matches
        combined_text = "\n".join(all_combined)

        urls = sorted(list(set(cls.URL_REGEX.findall(combined_text))))
        ips = sorted(list(set(cls.IP_REGEX.findall(combined_text))))
        # Ignorar IPs comuns de loopback / broadcast se forem irrelevantes
        ips = [ip for ip in ips if ip not in ("0.0.0.0", "255.255.255.255", "127.0.0.1")]
        emails = sorted(list(set(cls.EMAIL_REGEX.findall(combined_text))))

        paths = []
        for line in all_combined:
            for p in cls.PATH_REGEX.findall(line):
                if len(p) > 6 and p not in paths:
                    paths.append(p)

        return StringsResult(
            total_strings=len(ascii_matches) + len(unicode_matches),
            ascii_strings=ascii_matches[:max_strings],
            unicode_strings=unicode_matches[:max_strings],
            urls=urls,
            ip_addresses=ips,
            file_paths=paths[:100],
            emails=emails,
        )

    @classmethod
    def extract_from_file(cls, file_path: Union[str, Path], min_len: int = 4, max_strings: int = 5000) -> StringsResult:
        """Lê arquivo em blocos e extrai strings e padrões."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        with open(path, "rb") as f:
            data = f.read()

        return cls.extract_from_bytes(data, min_len=min_len, max_strings=max_strings)

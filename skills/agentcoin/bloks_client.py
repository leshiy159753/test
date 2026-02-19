"""
BLOKS Agent Mint API client.

Implements the full mint flow:

    1. ``get_mint_phase()``   – check current mint phase (whitelist / public / closed)
    2. ``get_pow_challenge()``– request a Proof-of-Work challenge token
    3. ``solve_pow()``        – brute-force the nonce that satisfies the difficulty
    4. ``verify_pow()``       – exchange solved PoW for a verified mint token
    5. ``mint()``             – perform the actual mint (includes WL signature when needed)

For whitelist phase the wallet signs an EIP-191 personal message
(``eth_account.messages.encode_defunct``) and the resulting signature hex
is added to the mint payload.

Threading note: all public methods are safe to call from a single thread.
The client is intentionally not thread-safe to keep the implementation simple.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

from bloks_config import BloksConfig

logger = logging.getLogger("bloks-mint")

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

MintPhase = str  # "whitelist" | "public" | "closed" | unknown string


@dataclass
class PowChallenge:
    """Raw PoW challenge returned by the API."""

    challenge_id: str
    challenge: str        # hex string seed / prefix
    difficulty: int       # number of leading zero bits required
    algorithm: str        # e.g. "sha256"
    expires_at: Optional[int] = None  # Unix timestamp, if provided


@dataclass
class PowSolution:
    """A solved PoW — challenge + discovered nonce."""

    challenge_id: str
    nonce: int
    hash_hex: str  # the winning hash (informational)


@dataclass
class MintResult:
    """Result of a successful mint call."""

    tx_hash: Optional[str]
    token_id: Optional[int]
    raw: dict  # full API response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _leading_zero_bits(digest: bytes) -> int:
    """Count the number of leading zero bits in *digest*."""
    count = 0
    for byte in digest:
        if byte == 0:
            count += 8
        else:
            # Count leading zeros in this byte
            count += 8 - byte.bit_length()
            break
    return count


def _solve_sha256_pow(challenge: str, difficulty: int) -> tuple[int, str]:
    """
    Find a *nonce* (≥ 0) such that SHA-256(challenge + str(nonce)) has at
    least *difficulty* leading zero bits.

    Args:
        challenge:  The challenge string (hex or arbitrary).
        difficulty: Required leading zero bits.

    Returns:
        (nonce, hash_hex) tuple.
    """
    nonce = 0
    prefix = challenge.encode()
    while True:
        candidate = prefix + str(nonce).encode()
        digest = hashlib.sha256(candidate).digest()
        if _leading_zero_bits(digest) >= difficulty:
            return nonce, digest.hex()
        nonce += 1


# ---------------------------------------------------------------------------
# Main client
# ---------------------------------------------------------------------------


class BloksMintClient:
    """
    HTTP client that drives the BLOKS Agent Mint API.

    Usage::

        cfg = load_bloks_config()
        client = BloksMintClient(cfg)
        result = client.run_mint_flow()

    Args:
        config: Fully-populated :class:`~bloks_config.BloksConfig`.
    """

    def __init__(self, config: BloksConfig) -> None:
        self.config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Wallet-Address": config.wallet_address,
            }
        )

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_mint_phase(self) -> MintPhase:
        """
        Query the current mint phase for the configured project.

        Returns:
            One of ``"whitelist"``, ``"public"``, ``"closed"``, or an
            unrecognised string returned by the server.

        Raises:
            requests.HTTPError: On non-2xx response.
            RuntimeError: If the phase field is absent from the response.
        """
        url = self._url("phase")
        params = {
            "projectId": self.config.project_id,
            "chainId": self.config.chain_id,
        }
        logger.debug("GET %s params=%s", url, params)

        data = self._get(url, params=params)

        phase = data.get("phase") or data.get("mintPhase") or data.get("status")
        if phase is None:
            raise RuntimeError(
                f"Could not find phase field in API response: {data}"
            )

        phase = str(phase).lower()
        logger.info("Current mint phase: %s", phase)
        return phase

    def get_pow_challenge(self) -> PowChallenge:
        """
        Request a fresh PoW challenge from the BLOKS API.

        Returns:
            A populated :class:`PowChallenge`.

        Raises:
            requests.HTTPError: On non-2xx response.
            KeyError: If required fields are missing from the response.
        """
        url = self._url("pow/challenge")
        payload: dict[str, Any] = {
            "projectId": self.config.project_id,
            "chainId": self.config.chain_id,
            "walletAddress": self.config.wallet_address,
        }
        logger.debug("POST %s body=%s", url, payload)

        data = self._post(url, payload)

        try:
            return PowChallenge(
                challenge_id=data["challengeId"],
                challenge=data["challenge"],
                difficulty=int(data["difficulty"]),
                algorithm=data.get("algorithm", "sha256").lower(),
                expires_at=data.get("expiresAt"),
            )
        except KeyError as exc:
            raise KeyError(
                f"Missing field {exc} in PoW challenge response: {data}"
            ) from exc

    def solve_pow(self, challenge: PowChallenge) -> PowSolution:
        """
        Brute-force a nonce that satisfies *challenge*.

        Currently supports ``sha256`` algorithm only (BLOKS default).

        Args:
            challenge: The challenge to solve.

        Returns:
            A :class:`PowSolution` with the discovered nonce.

        Raises:
            NotImplementedError: If the algorithm is not supported.
        """
        algo = challenge.algorithm
        if algo != "sha256":
            raise NotImplementedError(
                f"PoW algorithm '{algo}' is not supported. "
                "Only 'sha256' is currently implemented."
            )

        logger.info(
            "Solving PoW (difficulty=%d, algorithm=%s) …",
            challenge.difficulty,
            algo,
        )
        start = time.monotonic()
        nonce, hash_hex = _solve_sha256_pow(challenge.challenge, challenge.difficulty)
        elapsed = time.monotonic() - start

        logger.info(
            "PoW solved: nonce=%d hash=%s… in %.2fs",
            nonce,
            hash_hex[:16],
            elapsed,
        )
        return PowSolution(
            challenge_id=challenge.challenge_id,
            nonce=nonce,
            hash_hex=hash_hex,
        )

    def verify_pow(self, solution: PowSolution) -> str:
        """
        Submit the solved PoW to the verify endpoint.

        Args:
            solution: The solved :class:`PowSolution`.

        Returns:
            A *mint token* string (opaque) to be included in the mint call.

        Raises:
            requests.HTTPError: On non-2xx response.
            RuntimeError: If the token field is absent from the response.
        """
        url = self._url("pow/verify")
        payload: dict[str, Any] = {
            "challengeId": solution.challenge_id,
            "nonce": solution.nonce,
            "walletAddress": self.config.wallet_address,
            "projectId": self.config.project_id,
            "chainId": self.config.chain_id,
        }
        logger.debug("POST %s", url)

        data = self._post(url, payload)

        mint_token = data.get("mintToken") or data.get("token") or data.get("verifyToken")
        if mint_token is None:
            raise RuntimeError(
                f"Mint token missing from verify response: {data}"
            )

        logger.info("PoW verified. Mint token acquired.")
        return str(mint_token)

    def sign_whitelist_message(self, message: Optional[str] = None) -> str:
        """
        Sign an EIP-191 personal message for whitelist proof.

        If *message* is not supplied the canonical BLOKS whitelist message
        ``"BLOKS Whitelist Mint: <wallet_address>"`` is used — adjust if the
        project specifies a different format.

        Args:
            message: The exact UTF-8 string to sign. ``None`` → default.

        Returns:
            Signature hex string (``0x…``).
        """
        if message is None:
            message = (
                f"BLOKS Whitelist Mint: {self.config.wallet_address}"
            )

        signable = encode_defunct(text=message)
        signed = self.config.account.sign_message(signable)
        sig_hex: str = signed.signature.hex()
        if not sig_hex.startswith("0x"):
            sig_hex = "0x" + sig_hex

        logger.debug("Whitelist message signed (sig=%s…)", sig_hex[:18])
        return sig_hex

    def mint(
        self,
        mint_token: str,
        phase: MintPhase,
        whitelist_message: Optional[str] = None,
    ) -> MintResult:
        """
        Execute the mint request.

        Args:
            mint_token:         Verified PoW token from :meth:`verify_pow`.
            phase:              Current mint phase (``"whitelist"`` or ``"public"``).
            whitelist_message:  Optional custom WL message to sign. ``None`` → default.

        Returns:
            A :class:`MintResult` with tx hash / token ID.

        Raises:
            requests.HTTPError: On non-2xx response.
        """
        url = self._url("mint")
        payload: dict[str, Any] = {
            "projectId": self.config.project_id,
            "chainId": self.config.chain_id,
            "walletAddress": self.config.wallet_address,
            "mintToken": mint_token,
        }

        if phase == "whitelist":
            sig = self.sign_whitelist_message(whitelist_message)
            payload["whitelistSignature"] = sig
            payload["whitelistAddress"] = self.config.wallet_address
            logger.info("Whitelist phase: adding EIP-191 signature to payload.")

        logger.debug("POST %s", url)
        data = self._post(url, payload)

        tx_hash = (
            data.get("txHash")
            or data.get("transactionHash")
            or data.get("tx_hash")
        )
        token_id_raw = data.get("tokenId") or data.get("token_id")
        token_id: Optional[int] = int(token_id_raw) if token_id_raw is not None else None

        logger.info(
            "Mint successful! tx=%s tokenId=%s",
            tx_hash or "n/a",
            token_id if token_id is not None else "n/a",
        )
        return MintResult(tx_hash=tx_hash, token_id=token_id, raw=data)

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run_mint_flow(
        self,
        dry_run: bool = False,
        whitelist_message: Optional[str] = None,
    ) -> Optional[MintResult]:
        """
        Execute the complete mint flow end-to-end:

        1. Check phase (abort if ``"closed"``).
        2. Request PoW challenge.
        3. Solve PoW locally.
        4. Verify solution → receive mint token.
        5. Mint (with WL signature if whitelist phase).

        Args:
            dry_run:            If ``True``, stop after verifying PoW; do not mint.
            whitelist_message:  Custom WL message; ``None`` → canonical default.

        Returns:
            :class:`MintResult` on success, ``None`` on ``"closed"`` phase.

        Raises:
            RuntimeError: If the phase is unrecognised or mint fails.
            requests.HTTPError: On any non-2xx API response.
        """
        # Step 1 – phase check
        phase = self.get_mint_phase()

        if phase == "closed":
            logger.warning("Mint is CLOSED. Nothing to do.")
            return None

        if phase not in ("whitelist", "public"):
            logger.warning(
                "Unrecognised phase '%s'. Attempting mint anyway…", phase
            )

        # Step 2 – PoW challenge
        challenge = self.get_pow_challenge()

        # Step 3 – solve PoW
        solution = self.solve_pow(challenge)

        # Step 4 – verify
        mint_token = self.verify_pow(solution)

        if dry_run:
            logger.info(
                "[DRY RUN] Would mint with token=%s…  Stopping here.",
                mint_token[:12],
            )
            return None

        # Step 5 – mint
        result = self.mint(
            mint_token=mint_token,
            phase=phase,
            whitelist_message=whitelist_message,
        )
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        """Build a full API URL from a relative *path*."""
        return f"{self.config.api_base_url}/{path.lstrip('/')}"

    def _get(
        self,
        url: str,
        params: Optional[dict] = None,
    ) -> dict:
        """Perform a GET with retry logic. Returns parsed JSON dict."""
        return self._request("GET", url, params=params)

    def _post(self, url: str, body: dict) -> dict:
        """Perform a POST with retry logic. Returns parsed JSON dict."""
        return self._request("POST", url, json_body=body)

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        json_body: Optional[dict] = None,
    ) -> dict:
        """
        Send an HTTP request with exponential back-off retries.

        Args:
            method:     ``"GET"`` or ``"POST"``.
            url:        Full URL.
            params:     Query string parameters (GET).
            json_body:  JSON payload (POST).

        Returns:
            Parsed JSON response dict.

        Raises:
            requests.HTTPError: After all retries are exhausted.
        """
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self._session.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "?"
                logger.warning(
                    "HTTP %s error on %s %s (attempt %d/%d)",
                    status,
                    method,
                    url,
                    attempt,
                    self.config.max_retries,
                )
                # 4xx errors are fatal – no point retrying
                if exc.response is not None and exc.response.status_code < 500:
                    self._log_error_body(exc.response)
                    raise
                last_exc = exc

            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Request error on %s %s (attempt %d/%d): %s",
                    method,
                    url,
                    attempt,
                    self.config.max_retries,
                    exc,
                )
                last_exc = exc

            if attempt < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** (attempt - 1))
                logger.debug("Retrying in %.1fs …", delay)
                time.sleep(delay)

        raise requests.HTTPError(
            f"All {self.config.max_retries} attempts failed for {method} {url}"
        ) from last_exc

    @staticmethod
    def _log_error_body(response: requests.Response) -> None:
        """Log a sanitised snippet of an error response body."""
        try:
            body = response.json()
            msg = body.get("message") or body.get("error") or str(body)
        except Exception:
            msg = response.text[:200]
        logger.error("API error body: %s", msg)

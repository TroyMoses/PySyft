# stdlib
import secrets

# third party
from result import Err
from result import Ok
from result import Result

# relative
from ...client.client import SyftClient
from ...serde.serializable import serializable
from ...types.syft_object import SYFT_OBJECT_VERSION_1
from ..context import ChangeContext
from ..request.request import Change
from ..response import SyftError
from ..response import SyftSuccess
from .node_peer import NodePeer
from .routes import NodeRoute


@serializable()
class AssociationRequestChange(Change):
    __canonical_name__ = "AssociationRequestChange"
    __version__ = SYFT_OBJECT_VERSION_1

    self_node_route: NodeRoute
    remote_peer: NodePeer
    challenge: bytes

    __repr_attrs__ = ["self_node_route", "remote_peer"]

    def _run(
        self, context: ChangeContext, apply: bool
    ) -> Result[tuple[bytes, NodePeer], SyftError]:
        # relative
        from .network_service import NetworkService

        if not apply:
            return Err(
                SyftError(message="Undo not supported for AssociationRequestChange")
            )

        service_ctx = context.to_service_ctx()

        try:
            remote_client: SyftClient = self.remote_peer.client_with_context(
                context=service_ctx
            )
            random_challenge = secrets.token_bytes(16)
            remote_res = remote_client.api.services.network.ping(
                challenge=random_challenge
            )
        except Exception as e:
            return SyftError(message="Remote Peer cannot ping peer:" + str(e))

        if isinstance(remote_res, SyftError):
            return Err(remote_res)

        challenge_signature = remote_res

        # Verifying if the challenge is valid
        try:
            self.remote_peer.verify_key.verify_key.verify(
                random_challenge, challenge_signature
            )
        except Exception as e:
            return Err(SyftError(message=str(e)))

        network_stash = service_ctx.node.get_service(NetworkService).stash

        result = network_stash.update_peer(
            service_ctx.node.verify_key, self.remote_peer
        )
        if result.is_err():
            return Err(SyftError(message=str(result.err())))

        # this way they can match up who we are with who they think we are
        # Sending a signed messages for the peer to verify
        self_node_peer = self.self_node_route.validate_with_context(context=service_ctx)

        if isinstance(self_node_peer, SyftError):
            return Err(self_node_peer)

        # Q,TODO: Should the returned node peer also be signed
        # as the challenge is already signed
        challenge_signature = service_ctx.node.signing_key.signing_key.sign(
            self.challenge
        ).signature

        return Ok([challenge_signature, self_node_peer])

    def apply(self, context: ChangeContext) -> Result[SyftSuccess, SyftError]:
        return self._run(context, apply=True)

    def undo(self, context: ChangeContext) -> Result[SyftSuccess, SyftError]:
        return self._run(context, apply=False)

    def __repr_syft_nested__(self) -> str:
        return f"Request for connection from : {self.remote_peer.name}"

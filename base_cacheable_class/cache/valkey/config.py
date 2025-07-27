from dataclasses import dataclass, field

from glide import GlideClientConfiguration, NodeAddress


@dataclass
class ValkeyClientConfig:
    """
    Simplified configuration class for Valkey client.
    Includes only essential settings; others use default values.
    """

    host: str = "localhost"
    port: int = 6379
    database_id: int = 0
    use_tls: bool = False
    request_timeout_ms: int | None = None
    client_name: str | None = None
    additional_nodes: list[tuple[str, int]] = field(default_factory=list)

    def to_glide_config(self) -> GlideClientConfiguration:
        """
        Convert ValkeyClientConfig to GlideClientConfiguration
        """
        addresses = [NodeAddress(host=self.host, port=self.port)]

        # Include additional nodes if present
        for host, port in self.additional_nodes:
            addresses.append(NodeAddress(host=host, port=port))

        config = GlideClientConfiguration(
            addresses=addresses,
            use_tls=self.use_tls,
            database_id=self.database_id,
        )

        # Optional settings
        if self.request_timeout_ms is not None:
            config.request_timeout = self.request_timeout_ms

        if self.client_name is not None:
            config.client_name = self.client_name

        return config

    @classmethod
    def localhost(cls, port: int = 6379, database_id: int = 0) -> "ValkeyClientConfig":
        return cls(host="localhost", port=port, database_id=database_id)

    @classmethod
    def remote(cls, host: str, port: int = 6379, use_tls: bool = False) -> "ValkeyClientConfig":
        return cls(host=host, port=port, use_tls=use_tls)

    @classmethod
    def cluster(cls, nodes: list[tuple[str, int]], use_tls: bool = False) -> "ValkeyClientConfig":
        if not nodes:
            raise ValueError("At least one node must be provided for cluster configuration")

        primary_host, primary_port = nodes[0]
        additional_nodes = nodes[1:] if len(nodes) > 1 else []

        return cls(host=primary_host, port=primary_port, additional_nodes=additional_nodes, use_tls=use_tls)

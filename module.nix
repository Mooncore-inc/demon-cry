self:
{ config, lib, pkgs, ... }:

let
  cfg = config.services.demon-cry;
  jsonFormat = pkgs.formats.json { };
  baseConfig = jsonFormat.generate "demon-cry-base.json" cfg.settings;
in
{
  options.services.demon-cry = {
    enable = lib.mkEnableOption "demon-cry OSINT agent";

    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
      defaultText = lib.literalExpression "demon-cry.packages.\${system}.default";
      description = "The demon-cry package to use.";
    };

    host = lib.mkOption {
      type = lib.types.str;
      default = "127.0.0.1";
      description = "Address the API listens on.";
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 8000;
      description = "Port the API listens on.";
    };

    openFirewall = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Whether to open {option}`port` in the firewall.";
    };

    apiKeyFile = lib.mkOption {
      type = lib.types.path;
      example = "/run/secrets/demon-cry-api-key";
      description = ''
        Path to a file containing the LLM provider API key. Passed to the
        service via systemd LoadCredential, so it never enters the Nix store.
      '';
    };

    masterKeyFile = lib.mkOption {
      type = lib.types.path;
      example = "/run/secrets/demon-cry-master-key";
      description = ''
        Path to a file containing the master key used for Bearer authentication
        on the API itself. An empty value disables authentication entirely — do
        not do that on a publicly reachable port.
      '';
    };

    settings = lib.mkOption {
      type = jsonFormat.type;
      default = { };
      example = {
        base_url = "https://api.deepseek.com/v1";
        model = "deepseek-chat";
      };
      description = ''
        Non-secret part of config.json. The api_key and master_key fields are
        filled in at startup from {option}`apiKeyFile` and {option}`masterKeyFile`.
      '';
    };

    searx = {
      enable = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = ''
          Run a local SearXNG instance via services.searx and point the agent at
          it. Requires services.searx.environmentFile to provide SEARXNG_SECRET.
        '';
      };

      port = lib.mkOption {
        type = lib.types.port;
        default = 8888;
        description = "Port of the local SearXNG instance.";
      };
    };
  };

  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.settings ? base_url && cfg.settings ? model;
        message = "services.demon-cry.settings must define base_url and model.";
      }
      {
        assertion = cfg.searx.enable -> config.services.searx.environmentFile != null;
        message = ''
          services.demon-cry.searx.enable requires services.searx.environmentFile
          containing SEARXNG_SECRET=<openssl rand -hex 32>.
        '';
      }
    ];

    services.demon-cry.settings.searxng_url = lib.mkIf cfg.searx.enable
      (lib.mkDefault "http://127.0.0.1:${toString cfg.searx.port}");

    services.searx = lib.mkIf cfg.searx.enable {
      enable = true;
      settings = {
        server = {
          port = cfg.searx.port;
          bind_address = "127.0.0.1";
          secret_key = "$SEARXNG_SECRET";
        };
        search.formats = [ "html" "json" ];
      };
    };

    systemd.services.demon-cry = {
      description = "demon-cry OSINT agent";
      wantedBy = [ "multi-user.target" ];
      wants = [ "network-online.target" ];
      after = [ "network-online.target" ] ++ lib.optional cfg.searx.enable "searx.service";

      environment.DEMON_CRY_CONFIG = "%t/demon-cry/config.json";

      preStart = ''
        umask 077
        ${lib.getExe pkgs.jq} \
          --rawfile api_key "$CREDENTIALS_DIRECTORY/api_key" \
          --rawfile master_key "$CREDENTIALS_DIRECTORY/master_key" \
          '. + {
             api_key: ($api_key | sub("\\s+$"; "")),
             master_key: ($master_key | sub("\\s+$"; ""))
           }' \
          ${baseConfig} > "$RUNTIME_DIRECTORY/config.json"
      '';

      serviceConfig = {
        ExecStart = "${lib.getExe cfg.package} --host ${cfg.host} --port ${toString cfg.port}";
        Restart = "on-failure";
        RestartSec = 5;

        DynamicUser = true;
        RuntimeDirectory = "demon-cry";
        RuntimeDirectoryMode = "0700";
        LoadCredential = [
          "api_key:${cfg.apiKeyFile}"
          "master_key:${cfg.masterKeyFile}"
        ];

        CapabilityBoundingSet = [ "" ];
        DevicePolicy = "closed";
        LockPersonality = true;
        NoNewPrivileges = true;
        PrivateDevices = true;
        PrivateTmp = true;
        PrivateUsers = true;
        ProcSubset = "pid";
        ProtectClock = true;
        ProtectControlGroups = true;
        ProtectHome = true;
        ProtectHostname = true;
        ProtectKernelLogs = true;
        ProtectKernelModules = true;
        ProtectKernelTunables = true;
        ProtectProc = "invisible";
        ProtectSystem = "strict";
        RestrictAddressFamilies = [ "AF_INET" "AF_INET6" "AF_UNIX" ];
        RestrictNamespaces = true;
        RestrictRealtime = true;
        RestrictSUIDSGID = true;
        SystemCallArchitectures = "native";
        SystemCallFilter = [ "@system-service" "~@privileged" ];
        UMask = "0077";
      };
    };

    networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];
  };
}

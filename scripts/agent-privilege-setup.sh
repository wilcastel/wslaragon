#!/bin/sh
# Administrator-only lifecycle for the fixed agent privilege helper.
set -eu

ROOT="/"
SOURCE_HELPER="scripts/agent-privilege-helper.py"
OWNER=0
HELPER_REL="usr/lib/wslaragon/agent-privilege-helper"
CONFIG_REL="etc/wslaragon/agent-privilege.json"
POLICY_REL="etc/sudoers.d/wslaragon-agent-privilege"
CONFIG_DIGEST_REL="etc/wslaragon/agent-privilege.json.sha256"
LEGACY_REL="etc/sudoers.d/wslaragon"

path() { printf '%s/%s\n' "$ROOT" "$1"; }
helper() { path "$HELPER_REL"; }
config() { path "$CONFIG_REL"; }
policy() { path "$POLICY_REL"; }
config_digest_file() { path "$CONFIG_DIGEST_REL"; }
legacy() { path "$LEGACY_REL"; }
is_tty() { [ -t 0 ] && [ -t 1 ]; }
fail() { printf '%s\n' "$1" >&2; exit 1; }

platform_ok() {
    [ "$(uname -s)" = Linux ] && ! uname -r | grep -qi microsoft &&
        grep -q '^ID=ubuntu$' /etc/os-release
}

verify_file() {
    expected_mode=$1 expected_digest=$2 target=$3
    [ -f "$target" ] && [ ! -L "$target" ] || return 1
    [ "$(stat -c '%u:%g:%a' "$target")" = "$OWNER:$OWNER:$expected_mode" ] || return 1
    [ "$(sha256sum "$target" | awk '{print $1}')" = "$expected_digest" ]
}

source_digest() { sha256sum "$SOURCE_HELPER" | awk '{print $1}'; }
policy_digest() {
    printf '%s ALL=(root) NOPASSWD: /usr/lib/wslaragon/agent-privilege-helper\n' "$(id -un)" |
        sha256sum | awk '{print $1}'
}

preflight() {
    is_tty || fail 'TTY required'
    [ "$(id -u)" != 0 ] || fail 'run from an administrator account, not a root shell'
    platform_ok || fail 'native Ubuntu required'
    [ -f "$SOURCE_HELPER" ] && [ ! -L "$SOURCE_HELPER" ] || fail 'helper source missing'
    [ ! -e "$(legacy)" ] || fail 'legacy policy conflict; disable or resolve explicitly'
    for artifact in "$(helper)" "$(config)" "$(config_digest_file)" "$(policy)"; do
        [ ! -e "$artifact" ] && [ ! -L "$artifact" ] || fail 'feature artifact conflict; disable or resolve explicitly'
    done
}

rollback() {
    digest=$1
    if [ -e "$(policy)" ] && verify_file 440 "$digest" "$(policy)"; then
        sudo rm -f -- "$(policy)"
    fi
    if [ -e "$(helper)" ] && verify_file 755 "$(source_digest)" "$(helper)"; then
        sudo rm -f -- "$(helper)"
    fi
    if [ -e "$(config_digest_file)" ]; then
        sudo rm -f -- "$(config_digest_file)" "$(config)"
    fi
}

bootstrap() {
    preflight
    stage=$(mktemp -d)
    trap 'rm -rf "$stage"' EXIT HUP INT TERM
    digest=$(source_digest)
    user=$(id -un)
    home=$(getent passwd "$user" | awk -F: '{print $6}')
    project=$(pwd -P)
    [ -n "$home" ] && [ -d "$project" ] || fail 'invalid local installation'
    sudo install -d -o "$OWNER" -g "$OWNER" -m 755 "$(dirname "$(helper)")" "$(dirname "$(config)")" "$(dirname "$(policy)")"
    sudo install -o "$OWNER" -g "$OWNER" -m 755 "$SOURCE_HELPER" "$stage/helper"
    verify_file 755 "$digest" "$stage/helper" || fail 'staged helper verification failed'
    sudo install -o "$OWNER" -g "$OWNER" -m 755 "$stage/helper" "$(helper)"
    verify_file 755 "$digest" "$(helper)" || { rollback "$(feature_digest)"; fail 'helper verification failed'; }
    printf '{"user":"%s","home":"%s","project_root":"%s","ssl_dir":"%s/.config/wslaragon/ssl","tld":".test","nginx_available":"/etc/nginx/sites-available","nginx_enabled":"/etc/nginx/sites-enabled","php_socket":"/run/php/php-fpm.sock","helper":"/usr/lib/wslaragon/agent-privilege-helper"}\n' "$user" "$home" "$project" "$home" > "$stage/config"
    config_digest=$(sha256sum "$stage/config" | awk '{print $1}')
    printf '%s\n' "$config_digest" > "$stage/config.sha256"
    sudo install -o "$OWNER" -g "$OWNER" -m 644 "$stage/config" "$(config)"
    sudo install -o "$OWNER" -g "$OWNER" -m 600 "$stage/config.sha256" "$(config_digest_file)"
    verify_file 644 "$config_digest" "$(config)" || { rollback "$config_digest"; fail 'config verification failed'; }
    printf '%s ALL=(root) NOPASSWD: /usr/lib/wslaragon/agent-privilege-helper\n' "$user" > "$stage/policy"
    sudo install -o "$OWNER" -g "$OWNER" -m 440 "$stage/policy" "$stage/policy.checked"
    sudo visudo -cf "$stage/policy.checked" >/dev/null || { rollback "$(feature_digest)"; fail 'sudoers validation failed'; }
    expected_policy_digest=$(policy_digest)
    sudo install -o "$OWNER" -g "$OWNER" -m 440 "$stage/policy.checked" "$(policy)"
    verify_file 440 "$expected_policy_digest" "$(policy)" || { rollback "$expected_policy_digest"; fail 'policy verification failed'; }
    printf '{"version":1,"op":"ready"}\n' | sudo -n -- /usr/lib/wslaragon/agent-privilege-helper | grep -qx '{"version":1,"ok":true,"code":"ok"}' || {
        rollback "$expected_policy_digest"; fail 'readiness probe failed';
    }
    printf 'agent privilege feature enabled\n'
}

status() {
    is_tty || fail 'TTY required'
    [ "$(id -u)" != 0 ] || fail 'run from an administrator account, not a root shell'
    if [ -e "$(helper)" ] && [ -e "$(config)" ] && [ -e "$(config_digest_file)" ] && [ -e "$(policy)" ]; then
        printf 'agent privilege feature configured\n'
        return 0
    fi
    printf 'agent privilege feature not configured\n'
    return 1
}

disable() {
    is_tty || fail 'TTY required'
    [ "$(id -u)" != 0 ] || fail 'run from an administrator account, not a root shell'
    verify_file 440 "$(policy_digest)" "$(policy)" || fail 'refusing unverified policy removal'
    verify_file 755 "$(source_digest)" "$(helper)" || fail 'refusing unverified helper removal'
    [ -f "$(config_digest_file)" ] && [ ! -L "$(config_digest_file)" ] &&
        [ "$(stat -c '%u:%g:%a' "$(config_digest_file)")" = "$OWNER:$OWNER:600" ] ||
        fail 'refusing unverified config removal'
    config_digest=$(cat "$(config_digest_file)" 2>/dev/null) || fail 'refusing unverified config removal'
    verify_file 644 "$config_digest" "$(config)" || fail 'refusing unverified config removal'
    sudo rm -f -- "$(policy)"
    sudo rm -f -- "$(helper)" "$(config)" "$(config_digest_file)"
    printf 'agent privilege feature disabled\n'
}

case "${1-}" in
    bootstrap) bootstrap ;;
    status) status ;;
    disable) disable ;;
    *) fail 'usage: agent-privilege-setup.sh bootstrap|status|disable' ;;
esac

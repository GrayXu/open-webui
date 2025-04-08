<script lang="ts">
    import { WEBUI_BASE_URL } from '$lib/constants';

    export let className = 'size-8';
    export let src = `${WEBUI_BASE_URL}/static/favicon.png`;

    function isTrustedSource(url: string): boolean {
        if (
            url.startsWith(WEBUI_BASE_URL) ||
            url.startsWith('https://www.gravatar.com/avatar/') ||
            url.startsWith('data:') ||
            url.startsWith('/')
        ) {
            return true;
        }
        try {
            const parsed = new URL(url);
            const baseHost = new URL(WEBUI_BASE_URL).hostname;
            const parts = baseHost.split('.');
            const rootDomain = parts.length >= 2 ? parts.slice(-2).join('.') : baseHost;

            if (parsed.hostname === rootDomain || parsed.hostname.endsWith('.' + rootDomain)) {
                return true;
            }
            if (parsed.hostname === 'ufileos.com' || parsed.hostname.endsWith('.ufileos.com')) {
                return true;
            }
        } catch (error) {
            return false;
        }
        return false;
    }

    $: resolvedSrc =
        src === ''
            ? `${WEBUI_BASE_URL}/static/favicon.png`
            : isTrustedSource(src)
            ? src
            : `/user.png`;
</script>

<img
    crossorigin="anonymous"
    src={resolvedSrc}
    class="{className} object-cover rounded-full -translate-y-[1px]"
    alt="profile"
    draggable="false"
/>
<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let className = 'size-8';
	export let src = `${WEBUI_BASE_URL}/static/favicon.png`;

	let webuiBaseUrlHostname = '';
	let webuiBaseUrlRootDomain = '';

	try {
		const baseUrlString = WEBUI_BASE_URL.startsWith('http://') || WEBUI_BASE_URL.startsWith('https://')
			? WEBUI_BASE_URL
			: `http://${WEBUI_BASE_URL}`; // Add default protocol if needed
		const url = new URL(baseUrlString);
		webuiBaseUrlHostname = url.hostname; // e.g., chat.grayxu.cn or localhost or 192.168.1.100
		const parts = webuiBaseUrlHostname.split('.');
		if (parts.length <= 1 || parts.every(part => /^\d+$/.test(part))) {
			 webuiBaseUrlRootDomain = webuiBaseUrlHostname;
		} else if (parts.length >= 2) {
			webuiBaseUrlRootDomain = parts.slice(-2).join('.'); // e.g., grayxu.cn
		}
	} catch (e) {
		console.error("Error parsing WEBUI_BASE_URL:", WEBUI_BASE_URL, e);
		if (typeof WEBUI_BASE_URL === 'string' && WEBUI_BASE_URL.startsWith('/')) {
			 webuiBaseUrlHostname = '';
			 webuiBaseUrlRootDomain = '';
		}
	}


	function isAllowedSrc(source: string): boolean {
		if (!source) return false; // Handle null/undefined/empty string

		// Allow relative paths starting with / (relative to web root)
		if (source.startsWith('/')) return true;
		// Allow data URIs
		if (source.startsWith('data:')) return true;

		// Allow sources starting exactly with WEBUI_BASE_URL (covers paths relative to base)
		if (source.startsWith(WEBUI_BASE_URL)) return true;

		// Allow Gravatar
		if (source.startsWith('https://www.gravatar.com/avatar/')) return true;

		// Check absolute URLs for domain rules
		try {
			const sourceUrl = new URL(source); // This requires source to be an absolute URL
			const sourceHostname = sourceUrl.hostname;
			if (webuiBaseUrlRootDomain && (sourceHostname === webuiBaseUrlRootDomain || sourceHostname.endsWith('.' + webuiBaseUrlRootDomain))) return true;
			if (webuiBaseUrlHostname && sourceHostname === webuiBaseUrlHostname) return true;
			if (sourceHostname === 'ufileos.com' || sourceHostname.endsWith('.ufileos.com')) return true;
		} catch (e) {
		}
		return false;
	}

	$: finalSrc = src === '' || src === null || src === undefined
		? `${WEBUI_BASE_URL}/static/favicon.png` // Default favicon if src is empty/null/undefined
		: isAllowedSrc(src)
			? src // Use the source if it's allowed
			: `/user.png`; // Fallback user icon if src is not allowed
</script>

<img
	crossorigin="anonymous"
	src={finalSrc} // Use the computed finalSrc
	class=" {className} object-cover rounded-full -translate-y-[1px]"
	alt="profile"
	draggable="false"
/>
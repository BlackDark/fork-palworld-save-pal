import { send } from '$lib/utils/websocketUtils';
import { getUpsState } from '$states/upsState.svelte';
import { MessageType } from '$types';
import { activeSkillsData } from './activeSkills.svelte';
import { buildingsData } from './buildings.svelte';
import { elementsData } from './elements.svelte';
import { expData } from './exp.svelte';
import { friendshipData } from './friendship.svelte';
import { itemsData } from './items.svelte';
import { labResearchData } from './labResearch.svelte';
import { mapObjects } from './mapObjects.svelte';
import { missionsData } from './missions.svelte';
import { palsData } from './pals.svelte';
import { passiveSkillsData } from './passiveSkills.svelte';
import { presetsData } from './presets.svelte';
import { technologiesData } from './technologies.svelte';
import { workSuitabilityData } from './workSuitability.svelte';

export const bootstrap = async () => {
	// Load all independent data files in parallel for maximum performance
	// This reduces bootstrap time from sum of all loads to max(load times)
	await Promise.all([
		presetsData.reset(),
		palsData.reset(),
		activeSkillsData.reset(),
		passiveSkillsData.reset(),
		technologiesData.reset(),
		elementsData.reset(),
		expData.reset(),
		friendshipData.reset(),
		itemsData.reset(),
		workSuitabilityData.reset(),
		buildingsData.reset(),
		mapObjects.reset(),
		labResearchData.reset(),
		missionsData.reset()
	]);

	// Load UPS state (may have dependencies, so load after other data)
	const upsState = getUpsState();
	await upsState.loadAll();

	// Send version and sync app state (non-blocking, can be sent in parallel)
	send(MessageType.GET_VERSION);
	send(MessageType.SYNC_APP_STATE);
};

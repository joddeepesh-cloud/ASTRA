export interface SpaceFact {
  id: string;
  text: string;
  category: 'PLANETS' | 'STARS' | 'GALAXIES' | 'COSMOLOGY' | 'OBSERVATORIES';
}

export const SPACE_FACTS: SpaceFact[] = [
  {
    id: 'fact-1',
    text: 'A day on Venus is longer than a year on Venus. Venus takes 243 Earth days to rotate once on its axis, but only 225 Earth days to complete an orbit around the Sun.',
    category: 'PLANETS',
  },
  {
    id: 'fact-2',
    text: 'Neutron stars can pack more mass than the Sun into a sphere roughly the size of a city—about 20 kilometers in diameter.',
    category: 'STARS',
  },
  {
    id: 'fact-3',
    text: 'Light from the Sun takes approximately 8 minutes and 20 seconds to travel 93 million miles (150 million km) to reach Earth.',
    category: 'COSMOLOGY',
  },
  {
    id: 'fact-4',
    text: 'The Milky Way galaxy is estimated to contain between 100 billion and 400 billion stars, spanning roughly 100,000 light-years in diameter.',
    category: 'GALAXIES',
  },
  {
    id: 'fact-5',
    text: 'The Milky Way and Andromeda galaxies are moving toward each other at roughly 110 kilometers per second and are expected to merge in about 4.5 billion years.',
    category: 'GALAXIES',
  },
  {
    id: 'fact-6',
    text: 'A teaspoon of neutron-star material would weigh approximately 6 billion tons on Earth because of its extreme nuclear density.',
    category: 'STARS',
  },
  {
    id: 'fact-7',
    text: 'The observable universe is estimated to contain over 2 trillion galaxies, stretching across 93 billion light-years of expanding spacetime.',
    category: 'COSMOLOGY',
  },
  {
    id: 'fact-8',
    text: 'Olympus Mons on Mars is the largest known volcano in the Solar System—nearly three times the height of Mount Everest.',
    category: 'PLANETS',
  },
  {
    id: 'fact-9',
    text: 'Supermassive black holes containing millions to billions of solar masses reside at the central cores of almost all large galaxies.',
    category: 'GALAXIES',
  },
  {
    id: 'fact-10',
    text: 'Light emitted by distant galaxies is stretched to longer redder wavelengths due to the metric expansion of space, a phenomenon known as cosmological redshift.',
    category: 'COSMOLOGY',
  },
  {
    id: 'fact-11',
    text: 'Sloan Digital Sky Survey (SDSS) has mapped the 3D positions of over 3 million astronomical objects, creating one of the most detailed 3D maps of the universe.',
    category: 'OBSERVATORIES',
  },
  {
    id: 'fact-12',
    text: 'Galaxy Zoo crowdsourced human classifications for over 900,000 galaxies from SDSS imaging, establishing the baseline training data for modern galaxy morphology models.',
    category: 'OBSERVATORIES',
  },
  {
    id: 'fact-13',
    text: 'Proxima Centauri, the closest known star to the Sun, is a red dwarf located approximately 4.24 light-years away from Earth.',
    category: 'STARS',
  },
  {
    id: 'fact-14',
    text: 'Saturn’s moon Titan has a thick atmosphere and lakes of liquid ethane and methane, making it the only body in the Solar System other than Earth with liquid on its surface.',
    category: 'PLANETS',
  },
  {
    id: 'fact-15',
    text: 'Gamma-ray bursts are the most energetic electromagnetic events known in the universe, releasing as much energy in seconds as the Sun will over its entire 10-billion-year lifespan.',
    category: 'STARS',
  },
  {
    id: 'fact-16',
    text: 'Barred spiral galaxies account for roughly two-thirds of all spiral galaxies in the local universe, including our own Milky Way.',
    category: 'GALAXIES',
  },
  {
    id: 'fact-17',
    text: 'Cosmic Microwave Background (CMB) radiation is the oldest thermal light in the universe, emitted roughly 380,000 years after the Big Bang.',
    category: 'COSMOLOGY',
  },
  {
    id: 'fact-18',
    text: 'Jupiter’s Great Red Spot is a giant anticyclonic storm larger than Earth that has been raging for at least 350 years.',
    category: 'PLANETS',
  },
  {
    id: 'fact-19',
    text: 'Gravitational lensing occurs when massive objects warp space around them, bending and magnifying the light of distant background galaxies.',
    category: 'COSMOLOGY',
  },
  {
    id: 'fact-20',
    text: 'James Webb Space Telescope (JWST) operates at Lagrange Point 2 (L2), nearly 1.5 million kilometers from Earth, observing in deep infrared light.',
    category: 'OBSERVATORIES',
  },
];

export function getRandomSpaceFact(): SpaceFact {
  try {
    const lastIndexStr = sessionStorage.getItem('astra_last_fact_index');
    const lastIndex = lastIndexStr !== null ? parseInt(lastIndexStr, 10) : -1;

    let newIndex = Math.floor(Math.random() * SPACE_FACTS.length);
    if (newIndex === lastIndex && SPACE_FACTS.length > 1) {
      newIndex = (newIndex + 1) % SPACE_FACTS.length;
    }

    sessionStorage.setItem('astra_last_fact_index', newIndex.toString());
    return SPACE_FACTS[newIndex];
  } catch {
    return SPACE_FACTS[0];
  }
}

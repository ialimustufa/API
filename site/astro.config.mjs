import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// The base path matches the repository name for GitHub Pages deployment.
export default defineConfig({
  site: 'https://ialimustufa.github.io',
  // Keep local development at http://localhost:4321/ while GitHub Pages uses /API/.
  base: process.env.NODE_ENV === 'development' ? undefined : '/API/',
  integrations: [
    starlight({
      title: 'API Course',
      description: 'Build a production-minded API with Python and FastAPI.',
      logo: {
        replacesTitle: true,
        src: './src/assets/logo.svg',
      },
      social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/ialimustufa/API' }],
      sidebar: [
        {
          label: 'Start here',
          items: [
            { label: 'Course overview', slug: 'index' },
            { label: 'Environment setup', slug: 'setup' },
          ],
        },
        {
          label: 'TaskBox API',
          items: [
            { label: 'Domain and routes', slug: 'taskbox/domain-and-routes' },
            { label: 'Authentication', slug: 'taskbox/authentication' },
            { label: 'Projects and roles', slug: 'taskbox/projects-and-roles' },
            { label: 'Cursor pagination', slug: 'taskbox/cursor-pagination' },
            { label: 'Signed webhooks', slug: 'taskbox/signed-webhooks' },
          ],
        },
        {
          label: 'Persistence lab',
          items: [
            { label: 'SQLite first', slug: 'persistence/sqlite-first' },
            { label: 'PostgreSQL with Docker', slug: 'persistence/postgresql' },
          ],
        },
        {
          label: 'Course modules',
          items: [
            { label: '05 · Authentication and security', slug: 'modules/05-auth-security' },
            { label: '06 · Persistence', slug: 'modules/06-persistence' },
            { label: '07 · Operations', slug: 'modules/07-operations' },
            { label: '08 · GraphQL and gRPC', slug: 'modules/08-graphql-grpc' },
            { label: '09 · Realtime APIs', slug: 'modules/09-realtime' },
            { label: '10 · Webhooks and events', slug: 'modules/10-webhooks-events' },
            { label: '11 · Capstone deployment', slug: 'modules/11-capstone-deployment' },
          ],
        },
      ],
    }),
  ],
});

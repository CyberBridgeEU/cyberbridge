# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default tseslint.config({
  languageOptions: {
    // other options...
    parserOptions: {
      project: ['./tsconfig.node.json', './tsconfig.app.json'],
      tsconfigRootDir: import.meta.dirname,
    },
  },
})
```

- Replace `tseslint.configs.recommended` to `tseslint.configs.recommendedTypeChecked` or `tseslint.configs.strictTypeChecked`
- Optionally add `...tseslint.configs.stylisticTypeChecked`
- Install [eslint-plugin-react](https://github.com/jsx-eslint/eslint-plugin-react) and update the config:

```js
// eslint.config.js
import react from 'eslint-plugin-react'

export default tseslint.config({
  // Set the react version
  settings: { react: { version: '18.3' } },
  plugins: {
    // Add the react plugin
    react,
  },
  rules: {
    // other rules...
    // Enable its recommended rules
    ...react.configs.recommended.rules,
    ...react.configs['jsx-runtime'].rules,
  },
})
```


## Docker Setup

This project can be run in a Docker container. The Dockerfile is configured to expose port 5173 for the Vite development server.

### Building the Docker Image

To build the Docker image, run the following command from the project root directory:

```bash
docker build -t cyberbridge-frontend .
```

### Running the Docker Container

To run the container and access the application, use:

```bash
docker run -p 5173:5173 cyberbridge-frontend
```

This will map port 5173 from the container to port 5173 on your host machine. You can then access the application at http://localhost:5173.

### Development vs Production

The current Dockerfile is configured for development mode. For production deployment, you might want to:

1. Use a multi-stage build
2. Serve the static files using a lightweight web server like Nginx
3. Configure proper environment variables

Example of a production-ready command (after building):

```bash
docker run -p 80:80 cyberbridge-frontend-prod
```

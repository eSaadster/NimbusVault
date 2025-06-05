# AGENTS.md - NimbusVault Project

## Project Overview

### Description
NimbusVault is a [brief description of your project - e.g., "cloud-based data management platform that provides secure storage and analytics capabilities"]. The system focuses on [key features like scalability, security, performance, etc.].

### Main Technologies
- **Backend**: [e.g., Node.js, Python, Go, Java]
- **Frontend**: [e.g., React, Vue.js, Angular]
- **Database**: [e.g., PostgreSQL, MongoDB, Redis]
- **Cloud/Infrastructure**: [e.g., AWS, Docker, Kubernetes]
- **Other**: [e.g., GraphQL, REST APIs, WebSockets]

### Architecture Overview
```
[Describe your architecture - e.g.,]
├── Frontend (React SPA)
├── API Gateway
├── Microservices
│   ├── Authentication Service
│   ├── Data Processing Service
│   └── Analytics Service
├── Database Layer
└── External Integrations
```

## Development Setup

### Prerequisites
- [Runtime version - e.g., Node.js 18+, Python 3.9+]
- [Package manager - e.g., npm, yarn, pip]
- [Database - e.g., PostgreSQL 14+]
- [Other tools - e.g., Docker, Git]

### Installation
```bash
# Clone the repository
git clone [repository-url]
cd nimbusvault

# Install dependencies
[package manager install command]

# Setup database
[database setup commands]

# Install additional tools
[any additional setup]
```

### Environment Variables
Create a `.env` file with the following variables:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nimbusvault
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-jwt-secret
API_KEY=your-api-key

# External Services
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1

# Application
NODE_ENV=development
PORT=3000
LOG_LEVEL=debug
```

### Running Locally
```bash
# Start development server
npm run dev

# Run with database
docker-compose up -d
npm run dev

# Run tests
npm test

# Run specific service
npm run start:service-name
```

## Code Structure

### Directory Structure
```
nimbusvault/
├── src/
│   ├── components/          # Reusable UI components
│   ├── services/           # Business logic and API calls
│   ├── utils/              # Helper functions and utilities
│   ├── hooks/              # Custom React hooks (if applicable)
│   ├── types/              # TypeScript type definitions
│   ├── config/             # Configuration files
│   └── __tests__/          # Test files
├── public/                 # Static assets
├── docs/                   # Documentation
├── scripts/                # Build and utility scripts
├── .github/                # GitHub workflows
└── docker/                 # Docker configurations
```

### Key Files
- `src/index.js` - Application entry point
- `src/config/database.js` - Database configuration
- `src/services/auth.js` - Authentication logic
- `src/utils/logger.js` - Logging utilities
- `package.json` - Dependencies and scripts
- `docker-compose.yml` - Local development environment

### Module Organization
- **Services**: Contain business logic, should be pure functions when possible
- **Components**: UI components, should be small and focused on single responsibility
- **Utils**: Pure helper functions, well-tested and reusable
- **Types**: Centralized type definitions for consistency

## Coding Standards

### Code Style
- Use [ESLint/Prettier configuration] for consistent formatting
- Follow [specific style guide - e.g., Airbnb, Google]
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Prefer const over let, avoid var

### Naming Conventions
- **Files**: kebab-case for files (`user-service.js`)
- **Functions**: camelCase (`getUserData`)
- **Classes**: PascalCase (`UserManager`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_ATTEMPTS`)
- **Components**: PascalCase (`UserProfile`)

### Testing Requirements
- Minimum 80% code coverage
- Unit tests for all utility functions
- Integration tests for API endpoints
- E2E tests for critical user flows
- Test files should be co-located with source files

### Documentation Standards
- Use JSDoc comments for all public functions
- Include examples in documentation
- Keep README files up to date
- Document API endpoints with OpenAPI/Swagger

## Common Tasks

### Adding New Features
1. Create feature branch from `develop`
2. Add tests first (TDD approach)
3. Implement feature following existing patterns
4. Update documentation
5. Submit PR with comprehensive description

### Testing Procedures
```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test suite
npm test -- --grep "auth"

# Run tests in watch mode
npm run test:watch
```

### Deployment Process
1. Merge to `main` branch triggers staging deployment
2. Staging tests must pass
3. Manual approval for production deployment
4. Production deployment uses blue-green strategy

### Common Commands
```bash
# Development
npm run dev              # Start development server
npm run build           # Build for production
npm run lint            # Run linter
npm run format          # Format code

# Database
npm run db:migrate      # Run database migrations
npm run db:seed         # Seed database with test data
npm run db:reset        # Reset database

# Docker
docker-compose up       # Start all services
docker-compose down     # Stop all services
docker-compose logs     # View logs
```

## AI Agent Specific Instructions

### Preferred Approaches
1. **Security First**: Always validate inputs and sanitize outputs
2. **Error Handling**: Use consistent error handling patterns with proper logging
3. **Performance**: Consider caching and optimization in data-heavy operations
4. **Modularity**: Write small, focused functions that can be easily tested
5. **Type Safety**: Use TypeScript types consistently throughout the codebase

### Prioritization Guidelines
When making changes, prioritize in this order:
1. **Security vulnerabilities** - Fix immediately
2. **Bug fixes** - Address data corruption or system failures
3. **Performance improvements** - Optimize bottlenecks
4. **Feature enhancements** - Add new functionality
5. **Code refactoring** - Improve code quality without changing behavior

### Files to Avoid Modifying
- `src/config/production.js` - Production configuration (manual review required)
- `database/migrations/` - Historical migrations (create new ones instead)
- `.github/workflows/` - CI/CD pipelines (DevOps team manages)
- `public/static/` - Static assets managed by design team

### Required Patterns

#### API Response Format
```javascript
// Success response
{
  success: true,
  data: { /* response data */ },
  message: "Operation completed successfully"
}

// Error response
{
  success: false,
  error: {
    code: "VALIDATION_ERROR",
    message: "User-friendly error message",
    details: { /* additional error info */ }
  }
}
```

#### Error Handling
```javascript
try {
  const result = await riskyOperation();
  return result;
} catch (error) {
  logger.error('Operation failed', { error: error.message, stack: error.stack });
  throw new AppError('Operation failed', 'OPERATION_ERROR', 500);
}
```

#### Service Layer Pattern
```javascript
class UserService {
  async createUser(userData) {
    // Validate input
    const validation = validateUserData(userData);
    if (!validation.isValid) {
      throw new ValidationError(validation.errors);
    }
    
    // Business logic
    const hashedPassword = await hashPassword(userData.password);
    const user = await this.userRepository.create({
      ...userData,
      password: hashedPassword
    });
    
    // Return clean response
    return omit(user, ['password']);
  }
}
```

### Patterns to Avoid
- **Direct database queries in controllers** - Use service layer
- **Hardcoded values** - Use configuration files
- **Callback hell** - Use async/await
- **Global state mutations** - Use immutable updates
- **Deeply nested conditionals** - Extract to separate functions

## Examples

### Good: Service Implementation
```javascript
// services/user-service.js
const UserService = {
  async getUserById(id) {
    if (!id || !isValidObjectId(id)) {
      throw new ValidationError('Valid user ID is required');
    }
    
    const user = await User.findById(id);
    if (!user) {
      throw new NotFoundError('User not found');
    }
    
    return this.formatUserResponse(user);
  },
  
  formatUserResponse(user) {
    return {
      id: user._id,
      name: user.name,
      email: user.email,
      createdAt: user.createdAt
    };
  }
};
```

### Good: Component Implementation
```javascript
// components/UserProfile.jsx
const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await userService.getUserById(userId);
        setUser(userData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUser();
  }, [userId]);
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  
  return (
    <div className="user-profile">
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
};
```

### Don't: Anti-patterns
```javascript
// ❌ Don't do this - mixed concerns, no error handling
const badController = (req, res) => {
  const user = db.query('SELECT * FROM users WHERE id = ' + req.params.id);
  res.json(user);
};

// ❌ Don't do this - callback hell
getData(id, function(err, data) {
  if (err) throw err;
  processData(data, function(err, processed) {
    if (err) throw err;
    saveData(processed, function(err) {
      if (err) throw err;
      console.log('Done');
    });
  });
});
```

### Configuration Management
```javascript
// config/index.js
const config = {
  development: {
    database: {
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      name: process.env.DB_NAME || 'nimbusvault_dev'
    },
    logging: {
      level: 'debug'
    }
  },
  production: {
    database: {
      host: process.env.DB_HOST,
      port: process.env.DB_PORT,
      name: process.env.DB_NAME
    },
    logging: {
      level: 'error'
    }
  }
};

export default config[process.env.NODE_ENV || 'development'];
```

---

## Additional Notes for AI Agents

- Always check for existing similar functionality before creating new code
- Prefer updating existing functions over creating duplicates
- When adding new dependencies, justify the choice and consider bundle size
- Follow the principle of least privilege for database access and API permissions
- Consider backwards compatibility when modifying existing APIs
- Use feature flags for experimental features
- Always include appropriate logging for debugging and monitoring

For questions or clarifications, refer to the project documentation in `/docs` or consult with the development team.
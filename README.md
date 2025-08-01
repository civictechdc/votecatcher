# VoteCatcher ✓

**Open Source Campaign Infrastructure**

Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of grassroots campaigns. Democracy should be accessible to everyone.

## 🚀 Features

- **Signature Validation**: High-accuracy signature triaging using multimodal LLMs integrated with voter files
- **Grassroots Focused**: Built for community organizers and campaigns that need powerful tools without the high costs
- **Open Source**: Transparent, community-driven technology that strengthens democratic participation
- **PDF Processing**: OCR capabilities for processing petition documents
- **Fuzzy Matching**: Advanced name and address matching algorithms
- **Campaign Management**: Multi-campaign support with user isolation

## 🛠️ Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: Supabase (PostgreSQL, Auth, Storage, Edge Functions)
- **AI/ML**: OpenAI, Mistral, Gemini API integration
- **PDF Processing**: PDF.js for client-side PDF handling
- **UI Components**: Radix UI, Lucide React icons

## 📋 Prerequisites

Before deploying VoteCatcher, ensure you have:

- [Node.js](https://nodejs.org/) 18+ installed
- [Supabase CLI](https://supabase.com/docs/guides/cli) installed
- A Supabase project (free tier works)
- API keys for AI providers (OpenAI, Mistral, or Gemini)

## 🚀 Deployment Guide

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd votecatcher
npm install
```

### 2. Supabase Setup

#### Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your project URL and API keys

#### Install Supabase CLI
```bash
npm install -g supabase
```

#### Login to Supabase
```bash
supabase login
```

#### Link Your Project
```bash
supabase link --project-ref <your-project-ref>
```

### 3. Database Migration

Run the SQL scripts in the correct order:

```bash
# Connect to your Supabase project
supabase db reset

# Or run scripts manually in this order:
supabase db push --file supabase/1.\ campaign-schema.sql
supabase db push --file supabase/2.\ api-keys-schema.sql
supabase db push --file supabase/3.\ voter-records-schema.sql
supabase db push --file supabase/4.\ registered-voters.sql
supabase db push --file supabase/5.\ fuzzy-matching-schema.sql
```

**Migration Order:**
1. `campaign-schema.sql` - Creates campaign table and base functions
2. `api-keys-schema.sql` - API key management
3. `voter-records-schema.sql` - Voter data storage
4. `registered-voters.sql` - Petition signature data
5. `fuzzy-matching-schema.sql` - Matching algorithms

### 4. Deploy Edge Functions

```bash
# Deploy the voter file processing function
supabase functions deploy process-voter-file
```

### 5. Environment Configuration

Create a `.env.local` file based on `example.env.local`:

```bash
cp example.env.local .env.local
```

Fill in your environment variables:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Encryption (generate a secure 32-character hex string)
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef

# Optional: AI Provider API Keys
OPENAI_API_KEY=your-openai-key
MISTRAL_API_KEY=your-mistral-key
GEMINI_API_KEY=your-gemini-key
```

### 6. Storage Buckets Setup

The application automatically creates these storage buckets:
- `petitions` - For petition PDF files
- `voter-files` - For voter registration CSV files

### 7. Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### 8. Production Deployment

#### Option A: Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy

#### Option B: Other Platforms

```bash
# Build the application
npm run build

# Start production server
npm start
```

## 🔧 Configuration

### Authentication

VoteCatcher uses Supabase Auth. Configure authentication providers in your Supabase dashboard:
1. Go to Authentication > Settings
2. Configure your preferred providers (Email, Google, etc.)

### Row Level Security (RLS)

All tables have RLS enabled with policies that ensure:
- Users can only access data from campaigns they own
- Proper data isolation between campaigns
- Secure API key management
- No service role access - all operations use user authentication

### API Key Management

Users can store their own API keys for AI providers:
- OpenAI API Key
- Mistral API Key  
- Gemini API Key

Keys are encrypted and stored securely with user-level access control.

## 📁 Project Structure

```
votecatcher/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   ├── auth/              # Authentication pages
│   ├── workspace/         # Main application workspace
│   └── globals.css        # Global styles
├── components/            # Reusable UI components
│   └── ui/               # Radix UI components
├── lib/                   # Utility libraries
│   ├── supabase/         # Supabase client configuration
│   ├── encryption.ts     # Encryption utilities
│   └── hooks/            # Custom React hooks
├── supabase/             # Database and functions
│   ├── functions/        # Edge functions
│   └── *.sql            # Database schemas
└── types/                # TypeScript type definitions
```

## 🔒 Security Features

- **Row Level Security**: All data is protected by RLS policies
- **Encrypted API Keys**: User API keys are encrypted at rest
- **User Isolation**: Campaigns are isolated by user ownership
- **Secure File Upload**: Files are stored in private buckets with access controls
- **User-Based Authentication**: All API operations use authenticated user context
- **No Service Role Access**: Eliminated service role key dependency for enhanced security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. See [LICENSE](LICENSE) for details.

## 🆘 Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Join our community discussions

---

**VoteCatcher** - Making democracy accessible to everyone through open source technology.

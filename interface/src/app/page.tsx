import LoginForm from '@/components/LoginForm';

export default function Landing() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center gap-8 w-full max-w-md px-4">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Doc Chat</h1>
          <p className="text-muted-foreground">
            Chat with your documents using AI
          </p>
        </div>

        <LoginForm />
      </div>
    </div>
  );
}

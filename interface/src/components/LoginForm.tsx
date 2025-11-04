'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';

const passwordSchema = z.object({
  password: z.string().min(8, { message: 'Password must be at least 8 characters' }),
});

const usernameSchema = z.object({
  username: z.string().min(3, { message: 'Username must be at least 3 characters' }),
});

type PasswordSchema = z.infer<typeof passwordSchema>;
type UsernameSchema = z.infer<typeof usernameSchema>;

export default function LoginForm() {
  const [step, setStep] = useState<'password' | 'username'>('password');
  const [isExistingUser, setIsExistingUser] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const router = useRouter();
  const { checkPassword, login, register } = useAuth();

  const passwordForm = useForm<PasswordSchema>({
    mode: 'onChange',
    defaultValues: {
      password: '',
    },
  });

  const usernameForm = useForm<UsernameSchema>({
    mode: 'onChange',
    defaultValues: {
      username: '',
    },
  });

  const onPasswordSubmit = async (data: PasswordSchema) => {
    setError('');
    setIsLoading(true);
    
    try {
      const result = await checkPassword(data.password);
      setPassword(data.password);
      setIsExistingUser(result.exists);
      setStep('username');
    } catch (err: any) {
      setError(err.message || 'Failed to check password');
    } finally {
      setIsLoading(false);
    }
  };

  const onUsernameSubmit = async (data: UsernameSchema) => {
    setError('');
    setIsLoading(true);
    
    try {
      if (isExistingUser) {
        await login(data.username, password);
      } else {
        await register(data.username, password);
      }
      router.push('/home');
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setStep('password');
    setPassword('');
    setError('');
    passwordForm.reset();
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-md">
      {step === 'password' ? (
        <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              {...passwordForm.register('password')}
              disabled={isLoading}
            />
            {passwordForm.formState.errors.password && (
              <p className="text-sm text-red-500">
                {passwordForm.formState.errors.password.message}
              </p>
            )}
          </div>
          
          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}
          
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Checking...' : 'Continue'}
          </Button>
        </form>
      ) : (
        <form onSubmit={usernameForm.handleSubmit(onUsernameSubmit)} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              placeholder={isExistingUser ? 'Enter your username' : 'Choose a username'}
              {...usernameForm.register('username')}
              disabled={isLoading}
              autoFocus
            />
            {usernameForm.formState.errors.username && (
              <p className="text-sm text-red-500">
                {usernameForm.formState.errors.username.message}
              </p>
            )}
          </div>
          
          <p className="text-sm text-muted-foreground">
            {isExistingUser 
              ? 'Password recognized. Please enter your username to login.'
              : 'New password. Please choose a username to create your account.'}
          </p>
          
          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}
          
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={handleBack} disabled={isLoading}>
              Back
            </Button>
            <Button type="submit" className="flex-1" disabled={isLoading}>
              {isLoading ? 'Processing...' : isExistingUser ? 'Login' : 'Register'}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
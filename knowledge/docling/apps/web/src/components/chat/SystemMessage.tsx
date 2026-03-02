import React from 'react';

interface SystemMessageProps {
  content: string;
}

export const SystemMessage = React.memo<SystemMessageProps>(({ content }) => {
  return (
    <div className="flex justify-center my-2">
      <p className="text-text-muted text-sm font-body">{content}</p>
    </div>
  );
});

SystemMessage.displayName = 'SystemMessage';

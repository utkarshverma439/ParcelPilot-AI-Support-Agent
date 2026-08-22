import React from 'react';

const STATUS_STYLES = {
  'delivered': 'bg-green-100 text-green-800 border-green-200',
  'in_transit': 'bg-blue-100 text-blue-800 border-blue-200',
  'out_for_delivery': 'bg-orange-100 text-orange-800 border-orange-200',
  'delayed': 'bg-red-100 text-red-800 border-red-200',
  'pending': 'bg-gray-100 text-gray-800 border-gray-200',
  'booked': 'bg-purple-100 text-purple-800 border-purple-200',
  'picked_up': 'bg-indigo-100 text-indigo-800 border-indigo-200',
};

const STATUS_DOT = {
  'delivered': 'bg-green-500',
  'in_transit': 'bg-blue-500',
  'out_for_delivery': 'bg-orange-500',
  'delayed': 'bg-red-500',
  'pending': 'bg-gray-500',
  'booked': 'bg-purple-500',
  'picked_up': 'bg-indigo-500',
};

export default function ParcelCard({ data }) {
  const statusKey = (data.status || '').toLowerCase().replace(/\s+/g, '_');
  const statusStyle = STATUS_STYLES[statusKey] || STATUS_STYLES.pending;
  const dotColor = STATUS_DOT[statusKey] || STATUS_DOT.pending;

  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm max-w-sm my-3">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center">
          <span className="text-xl">📦</span>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Parcel</p>
          <p className="text-sm font-bold text-gray-900">{data.tracking_id || data.order_id || 'Unknown'}</p>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">Status</p>
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${statusStyle}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`}></span>
            {data.status || 'Unknown'}
          </span>
        </div>

        {data.location && (
          <div>
            <p className="text-xs text-gray-500 mb-1">📍 Current Location</p>
            <p className="text-sm font-medium text-gray-800">{data.location}</p>
          </div>
        )}

        {data.estimated_delivery && (
          <div>
            <p className="text-xs text-gray-500 mb-1">📅 Estimated Delivery</p>
            <p className="text-sm font-medium text-gray-800">{data.estimated_delivery}</p>
          </div>
        )}

        {data.last_update && (
          <div>
            <p className="text-xs text-gray-500 mb-1">🚚 Latest Update</p>
            <p className="text-sm font-medium text-gray-800">{data.last_update}</p>
          </div>
        )}

        {data.carrier && (
          <div>
            <p className="text-xs text-gray-500 mb-1">🚚 Carrier</p>
            <p className="text-sm font-medium text-gray-800">{data.carrier}</p>
          </div>
        )}

        {data.shipment_fee_inr && (
          <div>
            <p className="text-xs text-gray-500 mb-1">💰 Shipment Fee</p>
            <p className="text-sm font-medium text-gray-800">INR {data.shipment_fee_inr}</p>
          </div>
        )}
      </div>
    </div>
  );
}
